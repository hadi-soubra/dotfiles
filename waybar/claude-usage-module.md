# Waybar Claude Code Session Usage Module

## What It Does

Shows the current Claude.ai 5-hour session usage as a fill bar with percentage and time remaining, updated at :00 and :30 of every minute. Covers both Claude Code CLI usage and claude.ai web usage since they share the same server-side quota.

Example display: `███████░░░ 78% 2h16m`

---

## Files

| File | Purpose |
|------|---------|
| `~/.config/waybar/scripts/claude-usage.py` | Main script — fetches usage from API, outputs Waybar JSON |
| `~/.config/waybar/config.jsonc` | Waybar module definition (signal-driven, interval 0) |
| `~/.config/waybar/style.css` | Module styling |
| `~/.config/systemd/user/claude-waybar-refresh.service` | Oneshot service that sends SIGRTMIN+8 to Waybar |
| `~/.config/systemd/user/claude-waybar-refresh.timer` | Fires the service at :00 and :30 of every minute |

---

## How It Works

### Authentication

Two layers are needed to reach the claude.ai API:

1. **Cloudflare bypass** — The API is behind Cloudflare's managed bot challenge. Cookies from the Zen browser (specifically `cf_clearance`, `anthropic-device-id`, `__cf_bm`, `__ssid`) are read from the Zen profile's SQLite cookie store on every script run. As long as the user is logged into claude.ai in Zen, these are always fresh.

2. **API auth** — The endpoint `https://claude.ai/api/oauth/usage` requires `Authorization: Bearer <token>`. The token is the OAuth access token stored at `~/.claude/.credentials.json` under `claudeAiOauth.accessToken`. This is the same token Claude Code CLI uses and refreshes automatically.

### Zen Browser Cookie Path

```
/home/hadi/.config/zen/ow24iwue.Default (release)/cookies.sqlite
```

The script copies this to a temp file before reading (avoids SQLite lock conflicts with the open browser), and also copies `-wal`/`-shm` WAL files if present.

### API Response Format

```json
{
  "five_hour": {
    "utilization": 76.0,
    "resets_at": "2026-06-14T16:09:59.995862+00:00"
  },
  "seven_day": {
    "utilization": 9.0,
    "resets_at": "2026-06-16T10:59:59.995890+00:00"
  }
}
```

- `five_hour.utilization` — percentage used (0–100 float)
- `five_hour.resets_at` — ISO 8601 timestamp of when the session resets

### Update Mechanism

Waybar is configured with `"signal": 8` and `"interval": 0` — meaning it only refreshes the module when it receives `SIGRTMIN+8`. A systemd user timer fires `pkill -SIGRTMIN+8 waybar` at every :00 and :30, aligning updates to the wall clock rather than to Waybar's launch time.

---

## Waybar Config Entry

```jsonc
"custom/claude-usage": {
    "exec": "python3 ~/.config/waybar/scripts/claude-usage.py",
    "return-type": "json",
    "format": "{}",
    "interval": 0,
    "signal": 8,
    "tooltip": true
}
```

Position: `modules-left`, after `custom/next` (Spotify controls).

---

## CSS

```css
#custom-claude-usage { margin-left: 4px; }
#custom-claude-usage.inactive { color: #999999; }
```

Classes emitted by the script: `normal`, `warning` (≥60%), `critical` (≥80%), `inactive` (error/no session).

---

## Changing the Update Schedule

Edit `~/.config/systemd/user/claude-waybar-refresh.timer`:

```ini
[Timer]
OnCalendar=*:*:00
OnCalendar=*:*:30
AccuracySec=1s
```

Add or change `OnCalendar` lines to any second offset you want, then:

```bash
systemctl --user daemon-reload && systemctl --user restart claude-waybar-refresh.timer
```

---

## Common Issues

### Module shows `ℭ[–]`

The tooltip will contain the specific error. Common causes:

| Tooltip message | Cause | Fix |
|----------------|-------|-----|
| `HTTP 403` or Cloudflare HTML | `cf_clearance` cookie expired | Open claude.ai in Zen browser — navigating there refreshes the CF cookie automatically |
| `HTTP 401: invalid bearer token` | OAuth token expired | Run `claude` in terminal — Claude Code will refresh the token |
| `No claude.ai session in Zen browser` | Not logged into claude.ai in Zen | Log in at claude.ai |
| `No five_hour key in response` | API response format changed | Check the raw response and update the parser in the script |

### Module never updates

Check the timer is running:
```bash
systemctl --user status claude-waybar-refresh.timer
```

Check Waybar is receiving the signal:
```bash
# Manually trigger an update
pkill -SIGRTMIN+8 waybar
```

### Signal 8 conflicts with another Waybar module

Change `"signal": 8` in `config.jsonc` to any unused number (1–31), and update the `pkill` command in `claude-waybar-refresh.service` to match (`-SIGRTMIN+N`).

---

## Dependencies

- `python3` (stdlib only — no pip packages required)
- `sqlite3` CLI (for manual debugging; script uses Python's built-in sqlite3 module)
- Zen browser logged into claude.ai
- Claude Code CLI installed and authenticated (`~/.claude/.credentials.json` must exist)
- `systemd` user session
