# Production deployment

For automated first-time provisioning, start with `infra/terraform/README.md`. For a manual first-time setup, follow `AWS_GITHUB_DEPLOYMENT_GUIDE.md`. This document is the shorter release/operations reference after AWS, GitHub, DNS, and TLS are connected.

## Scope and result

Production runs the tested CertifyLK commit without changing domain behavior at deploy time. A single Ubuntu EC2 instance runs Nginx, standalone Next.js, FastAPI, PostgreSQL, and persistent upload storage through Docker Compose. Nginx is the only public container and serves one HTTPS origin; `/api/v1/*` is proxied to FastAPI and every other path to Next.js.

This is a single-host deployment for the authorized Track 1/Track 2 pilot. It is recoverable through logical backups and immutable application image tags, but it is not highly available. Product redesign status is tracked in `IMPLEMENTATION_PROGRESS.md`; infrastructure does not make unverified standard content trustworthy.

## Recorded production environment

| Item | Current value |
|---|---|
| Public URL | <https://certifylk.duckdns.org> |
| AWS region | `ap-south-1` |
| EC2 instance | `i-00e924bf43a9d1fbe` |
| Elastic IP | `3.108.242.97` |
| Verified release | `85a111a436928bc94a1d478cf3dcbaec0a66d03d` |
| AI mode | `gemini` (`gemini-3.6-flash`) with deterministic `mock` fallback |

The landing page and API health endpoints were verified for the recorded historical release. Re-verify both track entries and the current canonical workflow after every redesign deployment. The production environment file and all credentials remain EC2-only.

## Release invariants

- Application images are `ghcr.io/<owner>/certifylk-{frontend|backend}:<40-character-git-sha>`. No `latest` tag is used.
- Dockerfile base images and production PostgreSQL/Nginx images are pinned by digest; update those digests only through a reviewed, tested dependency change.
- PostgreSQL and upload volumes have explicit stable names (`POSTGRES_VOLUME_NAME` and `UPLOADS_VOLUME_NAME`). Deployment and rollback never run `docker compose down --volumes` or remove them.
- Alembic runs as the explicit `migrate` one-shot service before application containers are replaced. Catalogue synchronization is a second idempotent one-shot service.
- A database/upload backup is made before a deployment when the production database volume exists.
- Health checks must pass through the public HTTPS URL before the release is recorded.
- An unhealthy release automatically restores the prior application images when one is recorded. Schema downgrade is deliberately not automatic, so migrations must remain backward-compatible with the preceding release.

## Files

- `frontend/Dockerfile` and `backend/Dockerfile`: non-root runtime images with container health checks.
- `infra/production/docker-compose.yml`: private application/data networks, a backend-only outbound AI network, and persistent named volumes.
- `infra/production/nginx/`: HTTP-to-HTTPS redirect, ACME webroot, TLS termination, request limits, and reverse proxy.
- `infra/production/scripts/`: deployment, migration, health, backup, and rollback operations.
- `.github/workflows/ci.yml`: mandatory quality, test, audit, E2E, and image-build gates.
- `.github/workflows/deploy.yml`: immutable GHCR publish and AWS Systems Manager deployment after successful main-branch CI.

## One-time prerequisites

Complete `AWS_EC2_SETUP.md`, point the domain A/AAAA records at the EC2 Elastic IP, and create the GitHub `production` environment described in `CI_CD.md`. On EC2, the repository must be at `/opt/certifylk/repository`, owned by the `certifylk` operating-system user.

Create the protected production environment file:

```bash
cd /opt/certifylk/repository
sudo -H -u certifylk cp infra/production/.env.production.example infra/production/.env.production
sudo -H -u certifylk chmod 600 infra/production/.env.production
sudo -H -u certifylk editor infra/production/.env.production
```

Replace every example value. Use a long URL-safe PostgreSQL password and place the same value in `POSTGRES_PASSWORD` and the password component of `DATABASE_URL`. For live AI, set `AI_PROVIDER=gemini`, add `GEMINI_API_KEY`, keep the key only in this backend-side file, and use the stable `gemini-3.6-flash` model. `EVIDENCE_AI_TIMEOUT_SECONDS=8` and `EVIDENCE_AI_TOTAL_TIMEOUT_SECONDS=20` bound the optional evidence review independently from the main Gemini operation timeout. `AI_PROVIDER=mock` remains a supported deterministic production demonstration mode.

The backend is attached to the dedicated `ai_egress` Compose network so it can
make outbound HTTPS requests to Gemini. The application and data networks stay
internal, PostgreSQL remains unreachable from the internet, and no additional
host port is opened.

If GHCR packages are private, create `infra/production/.env.registry` on EC2 only:

```env
GHCR_USERNAME=github-user-with-package-read-access
GHCR_TOKEN=a_read_packages_only_token
```

```bash
sudo -H -u certifylk chmod 600 infra/production/.env.registry
```

The token needs package read access only. It is not passed to application containers. Public GHCR packages need no registry file.

## First certificate and first deployment

DNS must already resolve to the EC2 Elastic IP and ports 80/443 must be open. Before Nginx starts for the first time:

```bash
DOMAIN=certifylk.duckdns.org
EMAIL=operations@example.com
sudo install -d -m 755 /var/www/certbot
sudo certbot certonly --standalone --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN"
```

Set `IMAGE_TAG` to a tested 40-character commit whose images exist in GHCR, then run:

```bash
cd /opt/certifylk/repository
sudo -H -u certifylk bash infra/production/scripts/deploy.sh
```

After Nginx is healthy, change Certbot renewal to the served webroot and test it:

```bash
sudo certbot reconfigure --cert-name "$DOMAIN" --authenticator webroot --webroot-path /var/www/certbot
sudo certbot renew --dry-run
```

Install a Certbot deploy hook that reloads Nginx only after a successful renewal:

```bash
sudo install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
sudo install -m 755 /opt/certifylk/repository/infra/production/scripts/reload-nginx-after-renewal.sh \
  /etc/letsencrypt/renewal-hooks/deploy/certifylk-nginx
systemctl list-timers | grep certbot
```

## Routine deployment

Push to `main`. CI must succeed. The deployment workflow then:

1. Checks out the exact tested commit.
2. Builds and pushes frontend/backend images tagged only with that full commit SHA.
3. Uses GitHub OIDC for short-lived AWS credentials.
4. Sends an AWS Systems Manager command to EC2.
5. Checks out the exact commit on EC2 and invokes `deploy.sh` with its SHA.
6. Backs up, migrates, seeds, starts containers, and verifies the public HTTPS endpoints.

Manual server-side deployment is available for recovery:

```bash
cd /opt/certifylk/repository
git fetch --prune origin
git checkout --detach FULL_TESTED_COMMIT_SHA
IMAGE_TAG=FULL_TESTED_COMMIT_SHA bash infra/production/scripts/deploy.sh
```

Never deploy an untested SHA.

## Host recovery rules

- If public-repository cloning failed during initial cloud-init while the repository was private, make the repository public only when that is acceptable, then clone as the `certifylk` user or rerun the documented bootstrap steps. Do not place a GitHub token in Terraform state.
- If `.env.production` is missing, recreate it on EC2 from `.env.production.example`, generate the PostgreSQL password on the host, keep production in mock mode until verified, and set ownership/mode to `certifylk:certifylk` and `600`. Never print the file in CI or an SSM log.
- AWS `AWS-RunShellScript` uses `/bin/sh` for its command wrapper. Use portable `set -eu` there and invoke the repository deployment script explicitly with `bash`.
- GitHub environment values must not contain trailing spaces. The workflow normalizes and validates them, but operators should correct the stored values as well.
- Repairing a failed bootstrap does not justify deleting Docker volumes, Terraform state, the EC2 instance, or the Elastic IP. Preserve data and run the focused checks before redeploying.

## Operations

```bash
cd /opt/certifylk/repository
docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml ps
docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml logs --tail=200 nginx backend frontend postgres
bash infra/production/scripts/health-check.sh
bash infra/production/scripts/backup.sh
bash infra/production/scripts/rollback.sh
```

See `BACKUP_AND_RESTORE.md` before any restore and `RELEASE_CHECKLIST.md` before each public release.
