# Production security

## Security boundaries

The browser communicates only with Nginx over HTTPS. Nginx is the only container with host ports. Next.js, FastAPI, and PostgreSQL use internal Docker networks; PostgreSQL has no host port. Gemini and database credentials remain backend-only. Uploaded content remains untrusted data and cannot alter question, evidence, scoring, cost, or certification rules.

The application still has the locked guest UUID model and no authentication. Possession of an assessment UUID permits access to that assessment. A public operator must treat assessment URLs as sensitive bearer links, avoid sharing them, define a retention policy, and disclose this limitation. Adding accounts or changing the API is outside this deployment change.

## Secrets

- Never commit `.env.production`, `.env.registry`, Gemini keys, database passwords, deploy keys, TLS private keys, or backups.
- Production application secrets live only in `infra/production/.env.production` on EC2, owned by `certifylk` and mode `600`.
- A private GHCR read token lives separately in `.env.registry`, has package-read access only, and is not injected into application containers.
- GitHub authenticates to AWS using OIDC and short-lived credentials. Do not add AWS access-key secrets.
- Rotate the Gemini key, PostgreSQL password, GHCR token, GitHub deploy key, and TLS material after suspected disclosure. Database password rotation requires coordinated updates to PostgreSQL and `DATABASE_URL`.
- Do not print environment files, `docker inspect` output containing environment variables, or raw evidence in CI/SSM logs.

## Network and TLS

- Security-group ingress is limited to public ports 80 and 443. Port 80 exists only for ACME and redirects other traffic to HTTPS.
- Nginx permits TLS 1.2/1.3, sends HSTS and basic browser security headers, limits connections/requests, and caps request bodies just above the application’s 12 MB PDF limit.
- Do not enable HSTS preload without a separate domain-wide review.
- Only Nginx receives internet traffic. Do not add host port mappings for frontend, backend, or PostgreSQL.
- Certbot renewals use the mounted ACME webroot. Test renewal after every certificate or Nginx change.

## Container and host controls

- Frontend and backend run as UID/GID 10001, with read-only root filesystems, dropped Linux capabilities, `no-new-privileges`, and bounded temporary filesystems.
- The upload initializer runs briefly as root with only `CHOWN`; it cannot access PostgreSQL or the Docker socket.
- Application containers never mount the Docker socket.
- The `certifylk` host user can operate Docker and is therefore privileged. Restrict interactive access and protect its Git deploy key.
- Use an encrypted EBS volume, IMDSv2, current supported Ubuntu, security updates, and the SSM instance profile.

## Data protection

- PostgreSQL data, uploads, backups, and TLS material persist on the EC2/EBS host. EBS encryption protects data at rest; HTTPS protects browser traffic in transit.
- Application-level backup archives contain sensitive business and evidence data. Keep them mode `600`, encrypt any off-host copy, restrict access, and test restoration.
- Uploaded raw filenames are not used as storage paths. Nginx access logs omit query strings, while FastAPI logs path, status, latency, and request ID without document content.
- Define and execute a deletion/retention policy for guest assessments, uploads, logs, and backups before accepting real public submissions. Automatic assessment deletion is not part of the locked product scope.

## CI/CD protections

- Protect `main` and require every CI job.
- Keep GitHub Actions pinned to reviewed full commit SHAs.
- Protect the `production` environment, restrict it to `main`, and require review when supported.
- Scope the AWS OIDC trust to the exact repository and `production` environment, including immutable repository IDs when GitHub uses them.
- Scope `ssm:SendCommand` to the exact `AWS-RunShellScript` document and EC2 instances in the intended account/region carrying both `Project=CertifyLK` and `Environment=production` tags.
- Never deploy a tag not equal to a successful CI commit SHA.

## Terraform protections

- Never use AWS root access keys. The initial local Terraform run may use a dedicated IAM user's access key through a named AWS CLI profile. Keep it only in the local AWS credentials store, grant only the permissions required for provisioning where practical, enable MFA for console access, and deactivate, delete, or rotate the key when it is no longer needed. Temporary SSO/role credentials remain the preferred long-term option.
- Do not put AWS access keys in Terraform variables, provider blocks, state, plans, GitHub, workflow YAML, EC2 environment files, or repository files. GitHub deployment uses OIDC and short-lived credentials independently of the local Terraform profile.
- Terraform manages infrastructure identifiers and optional non-secret GitHub environment variables only. PostgreSQL, Gemini, GHCR, repository deploy keys, and TLS private keys are prohibited Terraform inputs.
- Treat local/remote Terraform state and saved plans as protected operational data even though this root deliberately excludes application secrets. State, plans, `.terraform/`, and the real `terraform.tfvars` are gitignored.
- Commit and review `.terraform.lock.hcl`. Run `terraform fmt -check`, `terraform validate`, and a human-reviewed `terraform plan` before apply.
- Stop if a plan proposes an unexpected instance, NAT Gateway, load balancer, RDS resource, instance replacement, volume deletion, or broader IAM permission.
- `terraform destroy` requires an exported verified backup and explicit confirmation of the account, region, state, and every destroy target.

## Incident minimums

If compromise is suspected: stop public ingress or Nginx, preserve logs, take an encrypted forensic snapshot, rotate affected credentials, inspect GitHub/AWS/SSM audit history, restore from a verified pre-incident backup if required, rerun the complete CI suite, and only then restore service. Do not delete evidence during initial containment.
