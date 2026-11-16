# MiniWin: lightweight Linux desktop + Wine + noVNC for Render.
# This is NOT Microsoft Windows. It launches only compatible 64-bit Windows apps.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    HOME=/home/app \
    WINEPREFIX=/home/app/.wine \
    WINEARCH=win64 \
    WINEDEBUG=-all

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    nginx \
    apache2-utils \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    fluxbox \
    xterm \
    x11-xserver-utils \
    wine \
    wine64 \
    fonts-wine \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
 && rm -f /etc/nginx/sites-enabled/default \
 && useradd -m -s /bin/bash app \
 && mkdir -p /home/app/Uploads /home/app/.fluxbox /opt/miniwin/www \
 && chown -R app:app /home/app

COPY nginx.conf /opt/miniwin/nginx.conf
COPY start.sh /opt/miniwin/start.sh
COPY server.py /opt/miniwin/server.py
COPY fluxbox-menu /home/app/.fluxbox/menu
COPY www/ /opt/miniwin/www/
RUN chmod +x /opt/miniwin/start.sh \
 && chown -R app:app /home/app

EXPOSE 10000
CMD ["/opt/miniwin/start.sh"]
