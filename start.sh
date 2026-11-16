#!/bin/sh
set -eu

: "${ACCESS_PASSWORD:?Set ACCESS_PASSWORD in Render environment variables before deploy}"

PORT="${PORT:-10000}"
case "$PORT" in
  ''|*[!0-9]*) echo 'PORT must be numeric' >&2; exit 1;;
esac

# Use one mandatory password for all browser endpoints, including WebSockets.
htpasswd -nbB admin "$ACCESS_PASSWORD" > /etc/nginx/.miniwin-htpasswd
chgrp www-data /etc/nginx/.miniwin-htpasswd
chmod 640 /etc/nginx/.miniwin-htpasswd
sed "s/__PORT__/${PORT}/g" /opt/miniwin/nginx.conf > /etc/nginx/conf.d/miniwin.conf

# Add a bit of style without loading a full desktop environment.
mkdir -p /home/app/Uploads
chown -R app:app /home/app/Uploads

export DISPLAY=:99 HOME=/home/app WINEPREFIX=/home/app/.wine WINEARCH=win64 WINEDEBUG=-all

runuser -u app -- env DISPLAY="$DISPLAY" HOME="$HOME" \
  Xvfb :99 -screen 0 1100x680x24 -nolisten tcp -ac &

# Xvfb creates its own local socket when ready.
i=0
while [ ! -S /tmp/.X11-unix/X99 ]; do
  i=$((i + 1))
  [ "$i" -lt 80 ] || { echo 'Xvfb did not start' >&2; exit 1; }
  sleep 0.25
done

runuser -u app -- env DISPLAY="$DISPLAY" HOME="$HOME" \
  fluxbox &
runuser -u app -- env DISPLAY="$DISPLAY" HOME="$HOME" \
  x11vnc -display :99 -rfbport 5900 -localhost -forever -shared -nopw \
  -quiet -noxdamage &

# All private ports listen only on loopback. Render publicly exposes nginx only.
websockify --web /usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900 &
runuser -u app -- env DISPLAY="$DISPLAY" HOME="$HOME" \
  WINEPREFIX="$WINEPREFIX" WINEARCH="$WINEARCH" WINEDEBUG="$WINEDEBUG" \
  python3 /opt/miniwin/server.py &

nginx -t
exec nginx -g 'daemon off;'
