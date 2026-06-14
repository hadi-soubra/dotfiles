if status is-interactive
    fastfetch
    thefuck --alias | source
    starship init fish | source
    set fish_greeting ""
# Commands to run in interactive sessions can go here
end
export PATH="$HOME/.local/bin:$PATH"
alias calc='bc -l'

fish_add_path ~/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin
