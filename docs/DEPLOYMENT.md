# Deployment

Nothing has been deployed publicly. The local application and build are the deliverable; the following configuration is ready for review, not evidence of a successful cloud deployment.

## Local production build

From `apps/web`, run `npm ci`, `npm run build`, then `npm start`. Start FastAPI separately using the README command. The Next.js build directory is `.build`; standalone packaging was avoided because the Windows environment rejected a nested build output operation. Normal Next.js server packaging builds successfully.

## Docker Compose

Copy `.env.example` to `.env`, install Docker, and run:

```sh
docker compose up --build
```

The frontend is bound to `127.0.0.1:3000`; the API is exposed only to the Compose network. A persistent named volume stores SQLite. The containers run as non-root users. Run one API worker because session and speech locks are in-process. Docker itself was unavailable in the build environment, so this configuration has not been smoke-tested with containers.

## Hosted private deployment

The numbered [setup guide](SETUP_STEP_BY_STEP.md) now includes a concrete DigitalOcean Docker server route. Use `docker compose -f compose.hosted.yaml up -d --build` for that route. The separate hosted file starts Caddy on ports 80/443, keeps both app services off public ports, forces production cookies, derives the HTTPS origin from `APP_DOMAIN`, and persists the database and TLS certificates. Run `scripts/prepare-env.py --private` first and review `.env`. Docker and the cloud deployment remain unexecuted in this workspace; validate the configuration and browser journey on the actual server.

Use a small VM or container platform that runs both Node and Python, supports a persistent filesystem and an HTTPS reverse proxy. The supplied stack is unsuitable for a frontend-only static host. Cloudflare Workers/Sites cannot directly run this FastAPI process; publishing only the frontend would not satisfy the brief.

Before hosting, generate a long independent internal API token and signing secret, set an access code, set `DEPLOYMENT_ENV=production`, set the exact HTTPS `APP_PUBLIC_URL`, and configure the matching `CORS_ORIGINS`. Secrets belong in the host's secret manager/runtime environment, not a repository or Docker image. Configure provider credentials only after restricting access. The backend and frontend fail closed when production security settings are incomplete.

Terminate HTTPS at the reverse proxy and forward only the Next.js port. The browser and proxy must agree on the configured public origin. Secure cookies require HTTPS. Keep the API private, restrict container/VM ingress, and set a request body limit of 2.1 MB and a timeout of at least 110 seconds. Do not log request bodies or full upstream query URLs. Configure backups and retention for the database volume.

This initial private gate is suitable for a small challenge demonstration. For public farmers, replace it with a reviewed account/consent flow, shared rate limits at the edge, per-user provider budgets, database migration to PostgreSQL, distributed session locking, access recovery and appropriate data retention. Do not scale to multiple API workers with the current in-process locks.

Run `pytest`, the frontend build and `scripts/live-smoke.py --allow-paid --wav …` before recording the live demo. Test both languages and multiple physical devices. Verify source freshness, loss assumptions, transcript corrections, provider failure fallbacks and private access. No deployment URL should be called verified until the actual hosted frontend-to-backend journey passes.
