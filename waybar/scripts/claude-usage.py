#!/usr/bin/env python3
import json, sqlite3, shutil, os, sys, urllib.request, urllib.error, ssl, tempfile, time
from datetime import datetime, timezone

COOKIE_DB = "/home/hadi/.config/zen/ow24iwue.Default (release)/cookies.sqlite"
CREDENTIALS = "/home/hadi/.claude/.credentials.json"
API_URL = "https://claude.ai/api/oauth/usage"
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
CF_COOKIES = {"cf_clearance", "anthropic-device-id", "__cf_bm", "__ssid"}


def inactive(msg):
    print(json.dumps({"text": "Loading...", "tooltip": msg, "class": "inactive"}))
    sys.exit(0)


def get_cf_cookies():
    tmp = tempfile.mktemp(suffix=".sqlite")
    try:
        shutil.copy2(COOKIE_DB, tmp)
        for ext in ("-wal", "-shm"):
            src = COOKIE_DB + ext
            if os.path.exists(src):
                shutil.copy2(src, tmp + ext)
        conn = sqlite3.connect(f"file:{tmp}?immutable=1", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%claude.ai'")
        result = {k: v for k, v in cur.fetchall() if k in CF_COOKIES}
        conn.close()
        return result
    finally:
        for path in [tmp, tmp + "-wal", tmp + "-shm"]:
            try:
                os.unlink(path)
            except Exception:
                pass


def get_oauth_token():
    with open(CREDENTIALS) as f:
        d = json.load(f)
    return d["claudeAiOauth"]["accessToken"]


def fetch_usage(cookies, token):
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
    req = urllib.request.Request(
        API_URL,
        headers={
            "Cookie": cookie_str,
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://claude.ai/settings/usage",
            "Authorization": f"Bearer {token}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        return json.loads(resp.read().decode())


def parse_reset(resets_at_str):
    ts = resets_at_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    secs = max(0, int((dt - datetime.now(timezone.utc)).total_seconds()))
    h, rem = divmod(secs, 3600)
    m = rem // 60
    return f"{h}h{m:02d}m", secs


def main():
    try:
        cookies = get_cf_cookies()
        token = get_oauth_token()
        data = fetch_usage(cookies, token)

        fh = data.get("five_hour")
        if not fh:
            inactive(f"No five_hour key in response: {json.dumps(data)[:200]}")

        percent = int(fh["utilization"])
        time_str, _ = parse_reset(fh["resets_at"])

        cls = "normal"
        if percent >= 80:
            cls = "critical"
        elif percent >= 60:
            cls = "warning"

        filled = percent * 10 // 100
        bar = "█" * filled + "░" * (10 - filled)

        tooltip = f"Current session: {percent}% used\nResets in {time_str}"
        print(json.dumps({"text": f"{bar} {percent}% {time_str}", "tooltip": tooltip, "class": cls}))

    except urllib.error.HTTPError as e:
        inactive(f"HTTP {e.code}: {e.read().decode()[:100]}")
    except Exception as e:
        inactive(f"Error: {e}")


if __name__ == "__main__":
    main()
