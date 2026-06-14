function tlauncher --wraps='java -jar /usr/games/tlauncher/starter-core.jar' --wraps='/usr/games/tlauncher/lib/jvm/jre/bin/java -jar /usr/games/tlauncher/starter-core.jar' --wraps='/usr/games/tlauncher/lib/jvm/jre/bin/java -jar /usr/games/tlauncher/starter-core.jar & disown' --description 'alias tlauncher=/usr/games/tlauncher/lib/jvm/jre/bin/java -jar /usr/games/tlauncher/starter-core.jar & disown'
    /usr/games/tlauncher/lib/jvm/jre/bin/java -jar /usr/games/tlauncher/starter-core.jar & disown $argv
end
