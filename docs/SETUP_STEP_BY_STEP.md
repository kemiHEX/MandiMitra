# MandiMitra: setup and private deployment, step by step

Use this sequence: run the demo on Windows, connect and test the real providers, then deploy a private HTTPS website. You can deploy demo mode before keys arrive; it will remain clearly labelled and speech recognition/synthesis will remain unavailable.

Recommended hosting: one DigitalOcean Docker server, with the website, Python backend and SQLite volume together. The supplied hosted configuration adds Caddy for HTTPS. A 2-vCPU / 4-GB server is a reasonable starting point for building and demonstrating this app; it is an engineering recommendation, not a measured capacity requirement. Review the provider's current price before creating the server. A domain and API usage may have separate costs. This guide does not purchase or publish anything for you.

**Verification boundary:** local application tests and browser checks passed. The hosted Docker/Caddy configuration has not yet been run on a real server. The instructions below include that final verification.

## 1. Install Node.js with npm on Windows

Python is already present on this machine. npm was not available in the terminal when checked.

Open the [official Node.js download page](https://nodejs.org/en/download), choose **Node.js 24 LTS**, **Windows**, and the installer matching your system (normally x64). Run the installer, keeping npm and the PATH option enabled. Then close and reopen PowerShell. The [npm installation guide](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm/) confirms that the Windows Node installer installs both tools.

Run:

```powershell
python --version
node --version
npm.cmd --version
```

Expected: Python 3.10 or newer, Node v24.x, and an npm version. `npm.cmd` avoids PowerShell's script execution-policy issue without changing your system's policy. If any command is unavailable, resolve that before continuing.

## 2. Open the project directory

The project already exists on this computer; no extraction is needed here:

```powershell
Set-Location 'C:\Users\sehaj\Documents\Codex\2026-11-09\files-pasted-by-the-user-build\outputs\mandimitra'
```

If using the ZIP on a different computer, extract it and open the folder containing `README.md`, `apps`, `services` and `compose.yaml` instead.

## 3. Install the backend dependencies

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services\api\requirements.txt
```

Wait for installation to finish without an error. You do not need to activate the environment.

## 4. Install the frontend dependencies

```powershell
Set-Location apps\web
npm.cmd ci
Set-Location ..\..
```

The final line returns you to the project root.

## 5. Create local settings

```powershell
.\.venv\Scripts\python.exe scripts\prepare-env.py
notepad .env
```

The helper creates `.env` from the example if necessary, generates missing internal/session secrets, and preserves existing nonempty values. It does not generate API keys.

Keep these values for the first run:

```dotenv
APP_MODE=demo
DEPLOYMENT_ENV=development
APP_PUBLIC_URL=http://localhost:3000
API_BASE_URL=http://127.0.0.1:8000
APP_ACCESS_CODE=
```

Leave the three provider keys empty for now. Keep the generated `API_INTERNAL_TOKEN` and `APP_SESSION_SECRET`. Save and close Notepad. The `.env` file contains private settings; do not send its contents in chat or include it in a public repository.

## 6. Start both services

```powershell
.\.venv\Scripts\python.exe scripts\dev.py
```

Leave this terminal open. Once the servers report that they are ready, open [MandiMitra locally](http://localhost:3000).

Expected: the MandiMitra page and a demonstration-mode banner. This local URL works on this computer only. Use `localhost`, matching the configured origin, rather than switching between addresses.

## 7. Check the demo

Choose **Try a tomato example**. With the fixed demonstration date still eligible, expect:

- Trader: ₹36,000.
- Khanna: ₹41,000 after ₹7,000 costs.
- Difference: ₹5,000; break-even: ₹1,075 per quintal.

Open **Costs & calculation**, change transport from ₹5,500 to ₹4,000, and update. Khanna should show ₹42,500. Enter “Chali nahi, chaudah quintal.” Quantity should become 14 and trader proceeds ₹12,600. Save and reopen the decision.

The sample is dated 8 November 2026. It intentionally becomes stale and eventually ages out; it is not rolled forward to resemble current data.

In a second PowerShell window, return to the same project directory and run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\verify-local.py
```

Expected for the delivered baseline: 108 automated tests and 14 local service checks. The local-check script assumes the initial ungated demo settings above. It uses its own disposable session.

## 8. Obtain the three provider keys when ready

| Key | Where to obtain it | What it enables |
|---|---|---|
| `GNANI_API_KEY` | Sign into the [Gnani dashboard](https://app.gnani.ai/) using the account you used for the playground. Obtain a speech API key with Prisma v3.0 and Timbre v3.0 access. | Transcription and spoken replies |
| `GROQ_API_KEY` | Open [Groq API Keys](https://console.groq.com/keys), sign in and create a key for this project. | Structured language understanding |
| `DATA_GOV_API_KEY` | Register/sign into [data.gov.in](https://www.data.gov.in/). Use the account's API key facility described in its [help page](https://www.data.gov.in/help). | Official mandi observations |

Gnani's [REST documentation](https://docs.gnani.ai/api/STT/speech-to-text) directs users to its API dashboard for a key. Playground success does not by itself prove that the key has programmatic access to every model.

Use **data.gov.in**, the Indian portal. Confirm access to the [daily mandi dataset](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi). A key alone does not guarantee that the resource is reachable or contains recent relevant records.

## 9. Enable private live mode locally

Stop the launcher using Ctrl+C. From the project root:

```powershell
.\.venv\Scripts\python.exe scripts\prepare-env.py --private
notepad .env
```

Set these lines, replacing only the three key placeholders with your actual keys:

```dotenv
APP_MODE=live
GNANI_API_KEY=YOUR_GNANI_KEY
GROQ_API_KEY=YOUR_GROQ_KEY
DATA_GOV_API_KEY=YOUR_DATA_GOV_KEY
GROQ_MODEL=openai/gpt-oss-120b
GNANI_TTS_MODEL=timbre-v3.0
GNANI_TTS_VOICE=Prakash
AGMARKNET_RESOURCE_ID=9ef84268-d588-465a-a308-a864a43d0070
```

Keep `DEPLOYMENT_ENV=development` and the local URL for this local HTTP test. The helper has also generated `APP_ACCESS_CODE`; read it locally and use that code when the website asks you to sign in. Preserve the generated internal token and signing secret.

Restart:

```powershell
.\.venv\Scripts\python.exe scripts\dev.py
```

## 10. Verify the real voice journey

At the local website, sign in, choose Punjabi, allow microphone access and record:

> Mere kol 40 quintal tamatar ne. Vyapari 900 rupaye prati quintal de reha hai. Main Ludhiana ton haan.

Stop recording, review the real transcript, correct any mistakes and send it. Confirm the trader's costs/loss assumptions and enter costs for each available market. Inspect source dates and units, then request the spoken answer. Correct 40 to 14 and verify that the comparison updates. Repeat in Hindi.

These actions can consume provider credits. Check transcription, actual returned observations and audible speech separately. An empty/stale official dataset is not a successful live comparison. Do not replace it with unlabelled sample data.

If you already have a suitable real recording, a diagnostic command is also available:

```powershell
.\.venv\Scripts\python.exe scripts\live-smoke.py --allow-paid --wav 'C:\path\to\punjabi.wav'
```

The file must be 0.1–30 seconds, mono, 16-bit PCM WAV at 16 kHz. The website performs conversion for its own microphone recordings. The diagnostic prints each provider's result; its TTS byte check does not replace listening in the browser.

If keys are still unavailable, retain `APP_MODE=demo` and continue with a labelled private demo deployment.

## 11. Create the hosting server

Use the [DigitalOcean Docker 1-Click option](https://docs.digitalocean.com/products/marketplace/catalog/docker/), which supplies Docker and Compose. Select a nearby region, a regular CPU plan with about 4 GB RAM as a starting point, and SSH-key login. Review the displayed recurring price before creating it. Save its public IPv4 address.

Follow the provider's SSH-key setup if you do not have one; keep the private key on your computer and give DigitalOcean only the public key. The [recommended server setup](https://docs.digitalocean.com/products/droplets/getting-started/recommended-droplet-setup/) also covers a non-root administrator and backups. These are server ownership settings you complete in your account.

Attach a cloud firewall allowing inbound TCP 80 and 443, and SSH/TCP 22 from your own IP. Leave required outbound connections enabled for API requests, package downloads and certificates. Do not expose 3000 or 8000. The supplied hosted Compose file does not publish those app ports.

## 12. Point a domain to the server

Use a domain you control, for example `mandimitra.yourdomain.com`. At its DNS provider, create an **A record** named `mandimitra` pointing to the server's IPv4 address. Use an unused subdomain; do not replace an unrelated existing site. Check for a conflicting AAAA record if IPv6 is not configured.

[DigitalOcean's DNS guide](https://docs.digitalocean.com/products/networking/dns/how-to/manage-records/) explains the A-record fields. Caddy needs the hostname to resolve to this server and ports 80/443 reachable to obtain its certificate. It then manages HTTPS renewal. [Caddy HTTPS documentation](https://caddyserver.com/docs/automatic-https)

You do not need to install Docker Desktop on Windows for this route; Docker runs on the remote server.

## 13. Upload the source archive

Use the newly updated `MandiMitra-source.zip`, which includes `compose.hosted.yaml`, `deploy/Caddyfile` and this guide. It excludes local `.env` settings, databases and dependencies.

In Windows PowerShell, replace `SERVER_IP` with the server's IPv4 address:

```powershell
scp 'C:\Users\sehaj\Documents\Codex\2026-11-09\files-pasted-by-the-user-build\outputs\MandiMitra-source.zip' root@SERVER_IP:/root/
ssh root@SERVER_IP
```

If your server uses a named administrator or a non-default SSH key, use that account and the `-i` option for your private-key file. The commands above assume the fresh Docker image's root login; the server setup guide describes the longer-term non-root administrator configuration. Verify the SSH host fingerprint against the provider's console when connecting for the first time.

## 14. Prepare settings on the server

The following are **Linux commands inside the SSH session**, not Windows PowerShell commands:

```sh
apt-get update
apt-get install -y unzip python3
mkdir -p /opt/mandimitra-release
unzip /root/MandiMitra-source.zip -d /opt/mandimitra-release
cd /opt/mandimitra-release/mandimitra
python3 scripts/prepare-env.py --private
nano .env
```

For the first deployment to this directory, unzip creates a fresh project. Do not overwrite an existing deployment blindly on a later update.

In `.env`, set:

```dotenv
APP_DOMAIN=mandimitra.yourdomain.com
APP_MODE=live
DEPLOYMENT_ENV=production
APP_PUBLIC_URL=https://mandimitra.yourdomain.com
CORS_ORIGINS=https://mandimitra.yourdomain.com
GNANI_API_KEY=YOUR_GNANI_KEY
GROQ_API_KEY=YOUR_GROQ_KEY
DATA_GOV_API_KEY=YOUR_DATA_GOV_KEY
```

Use your real domain without `https://` or a slash in `APP_DOMAIN`. Keep all three newly generated app secrets. For a demo deployment, set `APP_MODE=demo` and leave provider keys blank instead. In nano, press Ctrl+O, Enter to save, then Ctrl+X to exit.

The hosted Compose file supplies the internal API address, database path and HTTPS origin automatically. Do not replace its internal API address with `localhost`. Its private service networking uses Docker service names. [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/)

## 15. Validate and start the hosted app

Still in the server's project directory:

```sh
docker version
docker compose version
docker compose -f compose.hosted.yaml config --quiet
docker compose -f compose.hosted.yaml run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose -f compose.hosted.yaml up -d --build
docker compose -f compose.hosted.yaml ps
```

The quiet configuration check avoids displaying expanded secrets. The first build downloads dependencies and can take several minutes. Expect `api` to become healthy and `web`/`caddy` to be running. If any command fails, resolve that error before moving on. Do not repeatedly create new servers to troubleshoot the same application.

## 16. Open and verify HTTPS

Open `https://mandimitra.yourdomain.com` using your actual domain. Expected: a valid HTTPS connection and the MandiMitra access-code screen. Use the **server's** `APP_ACCESS_CODE`, which is separate from the locally generated one.

Verify the same flow as step 10 on both a computer and your intended demo phone. Save a decision, restart the containers with the command below, sign in again if needed, and confirm that the saved decision still appears in the same browser:

```sh
docker compose -f compose.hosted.yaml restart
```

Only after these checks should you call this a verified deployment. If it remains in demo mode, describe it as a deployed illustrative demo.

## 17. Logs, changes and data retention

To inspect startup or certificate failures:

```sh
docker compose -f compose.hosted.yaml logs --tail=80 api web caddy
```

Common fixes: a 401 usually means the app access code/key needs checking; a 403 saying invalid origin means the domain settings do not match the browser URL; a 502 usually means the web service is still building or failed; a certificate failure usually points to DNS or port access. A provider 401/403 is distinct from the website access-code gate. Read the specific error before changing settings.

After editing `.env`, apply it by recreating services, not merely restarting them:

```sh
docker compose -f compose.hosted.yaml up -d
```

The database is in the persistent `farmer-data` volume. Container replacement preserves it. Configure backups before storing real farmer information; a volume is not a backup. Do not use `docker compose down -v` as a troubleshooting step because it deletes persistent volumes, including saved decisions and certificate data.

This is a small private-demo deployment. Public rollout still needs stronger user accounts, shared abuse limits, operational monitoring and a reviewed privacy/retention process. See `LIMITATIONS.md` for the existing scope.

## What to send back when a step fails

Send the step number and the error message, with any keys, access codes, tokens or personal data removed. Do not send `.env` contents. For the first checkpoint, send only the output of `python --version`, `node --version` and `npm.cmd --version`.
