# MiniWin for Render

MiniWin is a minimal **Linux** graphical desktop remotely accessible in a browser, with **Wine** for some 64-bit `.exe` programs. It is **not Windows 10**, and it is not a VM.

## Features
- Debian 12 slim, Fluxbox, Xvfb, x11vnc, noVNC, Wine 64-bit.
- Web desktop with login password, an upload-and-launch portal (up to 32 MB per EXE), built-in Wine Notepad test.
- GUI apps appear on the browser desktop via noVNC.
- Uses one public Render port (default 10000); internal services listen on localhost.
- No real Windows license or ISO required.

## Deploy to Render (via GitHub)

1. Create an empty GitHub repository, e.g. `miniwin-render`.
2. Upload **the contents of this directory**, keeping the `Dockerfile` in the repository root (not a ZIP inside the repository).
3. In Render: **New > Web Service > Connect repository**.
4. Choose runtime **Docker**, branch `main`, and a suitable plan.
5. Under Environment, add `ACCESS_PASSWORD` = your **own strong, random secret password**. Do not save it in the repository. Optional: Render sets `PORT=10000` automatically.
6. Deploy and open `https://YOUR-SERVICE.onrender.com/`.
7. Enter **username `admin`** and the password from step 5.
8. Click **Проверить: Блокнот Wine** to test Wine. Then upload an x64 `.exe` and click **Пуск**.
9. If the embedded desktop is too small, click **На весь экран**.

Render's `Health Check Path` can be set to `/health` (no authentication required). `PORT` can be left at the default.

## Caveats
- Render Free has approximately 512 MiB RAM; GUI + Wine may be unstable or out of memory. It may require a paid plan with more RAM.
- Wine is a compatibility layer, not full Windows. **64-bit EXEs only** in this minimal build; many programs, games, applications needing .NET, hardware acceleration, drivers, anticheat or Windows services will not work.
- EXE uploader checks the Windows PE machine type, and refuses 32-bit EXE files. 32-bit support would require a much larger multiarch Wine installation.
- Free services spin down after inactivity, and local files + Wine environment are **lost** on sleep/restarts/redeploy. Keep a separate copy of your EXE and files. Free services do not support persistent disks.
- Access is protected by HTTP Basic Auth at nginx, including the WebSocket endpoint. Internal VNC has no independent password because it is loopback-only. Use HTTPS (Render provides it) and a unique secret. Do not share your deployment link/password.
- **Only run EXE files you trust.** A malicious Windows program may access the Wine environment and files in the container.
- This project has not been runtime-tested on Render. If the build hits package or memory limits, inspect Render's Deploy Logs.

## Local Docker run
```
docker build -t miniwin .
docker run --rm -p 10000:10000 -e ACCESS_PASSWORD='use-a-long-random-password' miniwin
```
Then visit `http://localhost:10000/`, username `admin`. Use HTTPS for any public deployment.

## Launch files in desktop terminal (optional)
Right-click the desktop to open the Fluxbox menu, or use the upload control on the website. Inside Linux terminal:
```
wine notepad.exe
wine /home/app/Uploads/myprogram.exe
```

## Notes on package size
The source project ZIP is small, but the built Docker image **is much larger** due to Wine. Render storage usage and RAM are separate constraints; Docker image size is not the same as runtime memory.
