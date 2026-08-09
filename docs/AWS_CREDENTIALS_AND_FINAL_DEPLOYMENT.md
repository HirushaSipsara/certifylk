# AWS credentials, GitHub connection, and final deployment

This guide starts from the current CertifyLK repository and explains exactly how to connect GitHub Actions to AWS and finish the first deployment.

It is an infrastructure/credential runbook and remains valid for the Track 1/Track 2 redesign. It does not verify standards content or prove the certificate-specific workflow is complete. Use `IMPLEMENTATION_PROGRESS.md`, `FULL_IMPLEMENTATION_PLAN.md`, and `RELEASE_CHECKLIST.md` for current product and smoke-test status.

For the automated alternative that creates the AWS roles, network, EC2, Elastic IP, optional DNS/budget, and GitHub environment variables, use `infra/terraform/README.md`. Keep this document as the credential-flow reference and troubleshooting fallback.

## Local credentials used to run Terraform

The first Terraform run may use the traditional local IAM flow:

```text
Dedicated IAM user -> IAM access key -> named AWS CLI profile -> Terraform
```

Configure and verify it from PowerShell:

```powershell
aws configure --profile certifylk-terraform
$env:AWS_PROFILE = "certifylk-terraform"
aws sts get-caller-identity --profile certifylk-terraform
```

Use an IAM user, never the AWS root user. The access key is stored by AWS CLI in `%UserProfile%\.aws\credentials`, outside the repository. Do not copy it into `terraform.tfvars`, a Terraform provider block, GitHub, or EC2. Follow the exact initialization, plan, and apply sequence in `infra/terraform/README.md`.

This local Terraform identity is separate from GitHub deployment authentication. Terraform creates the GitHub OIDC deployment role; after that, GitHub obtains temporary AWS credentials and does not use the IAM user's access key. Deactivate or delete the bootstrap key when you no longer need to run Terraform, or rotate it according to your operating policy.

## The most important rule

Do **not** add these long-term credentials to GitHub:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
```

CertifyLK uses GitHub OpenID Connect (OIDC). GitHub receives short-lived AWS credentials only while the production deployment job is running. The only AWS credential-like value stored in GitHub is the deployment IAM **role ARN**, and it is stored as an environment variable rather than a secret.

## 1. Understand where each value belongs

| Value | Storage location | Secret? |
|---|---|---|
| Local Terraform IAM access key | Local AWS CLI named profile (`%UserProfile%\.aws\credentials`) only | Yes |
| `AWS_REGION` | GitHub `production` environment variable | No |
| `AWS_ROLE_ARN` | GitHub `production` environment variable | No |
| `EC2_INSTANCE_ID` | GitHub `production` environment variable | No |
| `PRODUCTION_DOMAIN` | GitHub `production` environment variable | No |
| Temporary AWS credentials | Automatically issued through OIDC during the workflow | Yes, but never stored |
| `GITHUB_TOKEN` | Automatically created by GitHub Actions | Yes, automatically managed |
| PostgreSQL password | EC2 `infra/production/.env.production` | Yes |
| Gemini API key | EC2 `infra/production/.env.production` | Yes |
| GHCR read token, only for private packages | EC2 `infra/production/.env.registry` | Yes |
| Private-repository deploy key | EC2 `/opt/certifylk/.ssh/` | Yes |

The PostgreSQL password, Gemini key, GHCR token, and SSH private key never belong in GitHub variables, workflow YAML, frontend variables, or the Git repository.

## 2. Required values

Collect these before configuring GitHub:

```text
AWS account ID:       12-digit account ID
AWS region:           ap-south-1
EC2 instance ID:      i-xxxxxxxxxxxxxxxxx
Production domain:    app.your-domain.example
GitHub repository:    HirushaSipsara/certifylk
GitHub environment:   production
```

In the AWS console, the account ID is shown in the account menu. The instance ID is shown under **EC2 -> Instances**.

Use the same AWS region in EC2, Systems Manager, the IAM permissions policy, and the GitHub variable.

## 3. Create the EC2 Systems Manager role

This role is attached to the EC2 instance. It is not the GitHub role.

1. Open **AWS Console -> IAM -> Roles**.
2. Choose **Create role**.
3. Trusted entity type: **AWS service**.
4. Use case: **EC2**.
5. Search for and select `AmazonSSMManagedInstanceCore`.
6. Choose **Next**.
7. Role name: `certifylk-ec2-ssm`.
8. Create the role.

Attach it to the instance:

1. Open **EC2 -> Instances**.
2. Select the CertifyLK instance.
3. Choose **Actions -> Security -> Modify IAM role**.
4. Select `certifylk-ec2-ssm`.
5. Choose **Update IAM role**.

Wait a few minutes, then confirm the instance is online under **Systems Manager -> Fleet Manager -> Managed nodes**.

## 4. Create GitHub as an AWS OIDC provider

This establishes trust between the AWS account and GitHub's token service.

1. Open **AWS Console -> IAM -> Identity providers**.
2. Choose **Add provider**.
3. Provider type: **OpenID Connect**.
4. Provider URL:

   ```text
   https://token.actions.githubusercontent.com
   ```

5. Audience:

   ```text
   sts.amazonaws.com
   ```

6. Choose **Add provider**.

Create only one provider for this GitHub token URL in the AWS account. If it already exists, use the existing provider.

## 5. Create the GitHub deployment IAM role

This is the role GitHub Actions assumes temporarily.

1. Open **AWS Console -> IAM -> Roles**.
2. Choose **Create role**.
3. Trusted entity type: **Web identity**.
4. Identity provider: `token.actions.githubusercontent.com`.
5. Audience: `sts.amazonaws.com`.
6. Create the role with the name:

   ```text
   certifylk-github-deploy
   ```

Do not attach `AdministratorAccess`.

### Set the role trust policy

Open the new role, select **Trust relationships**, and choose **Edit trust policy**.

Replace `AWS_ACCOUNT_ID` with the actual 12-digit ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production"
        }
      }
    }
  ]
}
```

Save the policy.

Important:

- `HirushaSipsara/certifylk` is case-sensitive.
- `production` must exactly match the GitHub environment name.
- Do not replace the exact subject with a wildcard.

## 6. Give the GitHub role permission to deploy through SSM

Create a narrow customer-managed policy:

1. Open **IAM -> Policies -> Create policy**.
2. Select the **JSON** editor.
3. Replace `AWS_ACCOUNT_ID` and `EC2_INSTANCE_ID` below.
4. If the instance is outside Mumbai, replace every `ap-south-1` value too.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UseApprovedRunShellDocument",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ssm:ap-south-1::document/AWS-RunShellScript"
    },
    {
      "Sid": "SendCommandToExactCertifyLKInstance",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ec2:ap-south-1:AWS_ACCOUNT_ID:instance/EC2_INSTANCE_ID"
    },
    {
      "Sid": "ReadAndCancelDeploymentCommand",
      "Effect": "Allow",
      "Action": [
        "ssm:GetCommandInvocation",
        "ssm:CancelCommand"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Choose **Next**.
6. Policy name: `certifylk-github-deploy-ssm`.
7. Create the policy.
8. Open the `certifylk-github-deploy` role.
9. Choose **Permissions -> Add permissions -> Attach policies**.
10. Select `certifylk-github-deploy-ssm` and attach it.

Copy the role ARN from the role summary. It looks like:

```text
arn:aws:iam::123456789012:role/certifylk-github-deploy
```

This ARN becomes the GitHub `AWS_ROLE_ARN` variable.

## 7. Add the AWS connection values to GitHub

Open:

```text
GitHub -> HirushaSipsara/certifylk -> Settings -> Environments
```

1. Choose **New environment**.
2. Environment name:

   ```text
   production
   ```

3. Choose **Configure environment**.
4. Under **Environment variables**, add:

| Name | Example value |
|---|---|
| `AWS_REGION` | `ap-south-1` |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/certifylk-github-deploy` |
| `EC2_INSTANCE_ID` | `i-0123456789abcdef0` |
| `PRODUCTION_DOMAIN` | `app.your-domain.example` |

Use **environment variables**, not environment secrets, for these four non-secret identifiers.

Recommended environment protection:

1. Restrict deployment branches to `main`.
2. Add a required reviewer if the GitHub plan supports it.
3. Disable administrator bypass when appropriate.

The repository does not require AWS access-key secrets. If `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` was previously added, remove it after confirming no other workflow needs it.

## 8. Confirm the workflow has the correct AWS permissions

The repository file `.github/workflows/deploy.yml` already contains:

```yaml
permissions:
  contents: read
  id-token: write
```

`id-token: write` lets GitHub request an OIDC token. It does not grant AWS access by itself. AWS grants access only when the role trust policy, audience, repository, and environment all match.

Do not add access keys to the workflow.

## 9. Prepare the EC2 deployment host

Use **AWS Systems Manager -> Session Manager -> Start session**. Do not open SSH port 22.

Docker, Git, Certbot, and the `certifylk` user must be installed as described in `AWS_GITHUB_DEPLOYMENT_GUIDE.md`. Verify:

```bash
sudo docker version
sudo docker compose version
sudo systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service || \
sudo systemctl status amazon-ssm-agent.service
id certifylk
```

The required paths are:

```text
/opt/certifylk/repository
/var/lib/certifylk/releases
/var/backups/certifylk
/var/www/certbot
```

If they do not exist:

```bash
sudo adduser --system --group --home /opt/certifylk --shell /usr/sbin/nologin certifylk
sudo usermod -aG docker certifylk
sudo install -d -o certifylk -g certifylk -m 750 /opt/certifylk/repository
sudo install -d -o certifylk -g certifylk -m 700 /var/lib/certifylk/releases
sudo install -d -o certifylk -g certifylk -m 700 /var/backups/certifylk
sudo install -d -o root -g root -m 755 /var/www/certbot
```

## 10. Push and clone the repository

From the local workstation:

```powershell
Set-Location F:\Projects\certifylk
git add -A
git diff --cached --check
git status --short
git commit -m "Add CertifyLK production deployment workflow"
git push -u origin main
```

If this is the first push, the first deployment workflow may fail because EC2 is not fully prepared yet. That is safe. Complete the EC2 configuration below, then rerun the failed **Deploy production** workflow.

For a public GitHub repository, clone on EC2:

```bash
sudo -H -u certifylk git clone \
  https://github.com/HirushaSipsara/certifylk.git \
  /opt/certifylk/repository
```

For a private repository, configure the read-only deploy key described in `AWS_GITHUB_DEPLOYMENT_GUIDE.md`, then clone with SSH.

## 11. Add backend secrets on EC2

These secrets go on EC2, not GitHub.

```bash
cd /opt/certifylk/repository
sudo -H -u certifylk cp \
  infra/production/.env.production.example \
  infra/production/.env.production
sudo -H -u certifylk chmod 600 infra/production/.env.production
openssl rand -hex 32
sudo -H -u certifylk editor infra/production/.env.production
```

Configure at least:

```env
DOMAIN_NAME=app.your-domain.example
GHCR_OWNER=hirushasipsara
IMAGE_TAG=0000000000000000000000000000000000000000

POSTGRES_DB=certifylk
POSTGRES_USER=certifylk
POSTGRES_PASSWORD=PASTE_THE_GENERATED_HEX_PASSWORD
DATABASE_URL=postgresql+psycopg://certifylk:PASTE_THE_GENERATED_HEX_PASSWORD@postgres:5432/certifylk

AI_PROVIDER=mock
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
EVIDENCE_AI_TIMEOUT_SECONDS=8
EVIDENCE_AI_TOTAL_TIMEOUT_SECONDS=20
ALLOW_AI_FALLBACK=false
```

Use mock mode for the first deployment. After the public sample passes, edit the same EC2 file to enable Gemini:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
EVIDENCE_AI_TIMEOUT_SECONDS=8
EVIDENCE_AI_TOTAL_TIMEOUT_SECONDS=20
ALLOW_AI_FALLBACK=true
```

Check ownership without printing secrets:

```bash
stat -c '%a %U:%G %n' infra/production/.env.production
```

Expected:

```text
600 certifylk:certifylk infra/production/.env.production
```

## 12. Give EC2 permission to pull private GHCR images

The GitHub workflow publishes images using the automatically managed `GITHUB_TOKEN`. Do not create a token for the workflow.

If GHCR packages are private, EC2 needs a GitHub personal access token (classic) with only `read:packages`.

On EC2:

```bash
sudo -H -u certifylk editor /opt/certifylk/repository/infra/production/.env.registry
sudo -H -u certifylk chmod 600 /opt/certifylk/repository/infra/production/.env.registry
```

Contents:

```env
GHCR_USERNAME=your-github-user
GHCR_TOKEN=your_read_packages_only_token
```

If the two GHCR packages are public, do not create this file.

This is a GitHub package token stored only on EC2. It is unrelated to AWS OIDC.

## 13. Connect DNS and issue HTTPS

Associate an Elastic IP with the EC2 instance. At the DNS provider create:

```text
Type: A
Name: app
Value: YOUR_ELASTIC_IP
TTL: 300
```

Verify from Windows:

```powershell
Resolve-DnsName app.your-domain.example
```

After it returns the Elastic IP, issue the first certificate from the SSM session:

```bash
DOMAIN=app.your-domain.example
EMAIL=operations@your-domain.example

sudo certbot certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN"
```

Port 80 must be open in the EC2 security group. Do not continue until these exist:

```bash
sudo test -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
sudo test -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
```

## 14. Validate the EC2 configuration before deployment

```bash
cd /opt/certifylk/repository

sudo -H -u certifylk git fetch --prune origin
sudo -H -u certifylk git checkout --detach origin/main

sudo -H -u certifylk docker compose \
  --env-file infra/production/.env.production \
  -f infra/production/docker-compose.yml \
  --profile operations config --quiet
```

Do not run `docker compose config` without `--quiet` in screenshots or shared logs because rendered application environments may contain secrets.

## 15. Run the GitHub deployment

Open **GitHub -> Actions**.

The sequence is:

```text
CI
  Backend checks
  Frontend checks
  Mock-AI happy path
  Terraform checks
  Production container builds

Deploy production
  Publish immutable images
  Authenticate to AWS with GitHub OIDC
  Send deployment command through SSM
  Run deploy.sh on EC2
```

The deployment workflow runs only after a successful `CI` workflow caused by a push to `main`.

If the first deployment failed during bootstrap:

1. Finish EC2, `.env.production`, GHCR, DNS, and certificate preparation.
2. Open the failed **Deploy production** workflow run.
3. Choose **Re-run all jobs**.
4. Approve the `production` environment if prompted.

Do not manually create an image tagged `latest`. Both images must use the exact 40-character tested commit SHA.

## 16. How to recognize a successful OIDC connection

In the `Deploy production` workflow, the step **Authenticate to AWS with GitHub OIDC** should pass without showing an access key.

Common errors:

### `Not authorized to perform sts:AssumeRoleWithWebIdentity`

Check:

- `AWS_ROLE_ARN` contains the correct AWS account ID and role name;
- the provider URL is exactly `https://token.actions.githubusercontent.com`;
- audience is exactly `sts.amazonaws.com`;
- trust-policy subject is exactly `repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production`;
- GitHub environment is exactly `production`.

### `AccessDeniedException` for `ssm:SendCommand`

Check:

- permission-policy region;
- AWS account ID;
- exact EC2 instance ID and ARN;
- instance and GitHub role are in the same AWS account.

### SSM command remains pending or instance is not connected

Check:

- the EC2 role has `AmazonSSMManagedInstanceCore`;
- SSM Agent is running;
- the instance has outbound HTTPS access;
- the instance ID in GitHub is correct.

### GHCR returns `unauthorized`

Check:

- both package tags exist for the commit SHA;
- `.env.registry` exists only when required;
- the token has `read:packages`;
- organization SSO authorization is complete if applicable;
- `GHCR_OWNER=hirushasipsara` is lowercase.

## 17. Verify the finished deployment

From Windows:

```powershell
$domain = "app.your-domain.example"
Invoke-RestMethod "https://$domain/api/v1/health"
Invoke-RestMethod "https://$domain/api/v1/ready"
Start-Process "https://$domain/"
```

Expected statuses:

```text
health: ok
ready:  ready
```

Then choose the currently supported **Load Sample Report** action and confirm:

- readiness score;
- separate evidence completeness;
- at least one strength and one gap;
- LKR roadmap cost;
- projected readiness gain;
- certification disclaimer.

On EC2:

```bash
cd /opt/certifylk/repository
sudo -H -u certifylk docker compose \
  --env-file infra/production/.env.production \
  -f infra/production/docker-compose.yml ps
sudo -H -u certifylk bash infra/production/scripts/health-check.sh
```

Only Nginx should publish public ports. PostgreSQL, FastAPI, and Next.js must remain private.

## 18. Finish certificate renewal and backup setup

After the first successful deployment:

```bash
DOMAIN=app.your-domain.example

sudo certbot reconfigure \
  --cert-name "$DOMAIN" \
  --authenticator webroot \
  --webroot-path /var/www/certbot

sudo install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
sudo install -m 755 \
  /opt/certifylk/repository/infra/production/scripts/reload-nginx-after-renewal.sh \
  /etc/letsencrypt/renewal-hooks/deploy/certifylk-nginx

sudo certbot renew --dry-run

cd /opt/certifylk/repository
sudo -H -u certifylk bash infra/production/scripts/backup.sh
```

Verify the backup hashes using `BACKUP_AND_RESTORE.md`, then copy the backup to protected off-host storage.

## 19. Final connection checklist

- [ ] EC2 has the `certifylk-ec2-ssm` instance role.
- [ ] EC2 appears online in Systems Manager.
- [ ] GitHub OIDC provider exists in AWS.
- [ ] `certifylk-github-deploy` trust policy matches the exact repository and `production` environment.
- [ ] GitHub deployment role can call the approved SSM document only for the exact production instance ARN.
- [ ] GitHub `production` environment has all four required variables.
- [ ] GitHub contains no AWS access-key secrets.
- [ ] EC2 contains `.env.production` with mode `600`.
- [ ] Gemini key exists only on EC2 when enabled.
- [ ] EC2 can read private GHCR packages, or packages are public.
- [ ] DNS resolves to the Elastic IP.
- [ ] The Let's Encrypt certificate exists.
- [ ] CI passes for the exact SHA.
- [ ] OIDC authentication and SSM deployment pass.
- [ ] Public HTTPS health and sample workflow pass.
- [ ] Certificate renewal dry-run and backup verification pass.

## Related documents

- `AWS_GITHUB_DEPLOYMENT_GUIDE.md`: complete AWS host setup and operational guide.
- `PRODUCTION_DEPLOYMENT.md`: release behavior and routine commands.
- `CI_CD.md`: workflow gates and GitHub configuration.
- `AWS_EC2_SETUP.md`: focused EC2/IAM reference.
- `SECURITY.md`: production security boundaries.
- `BACKUP_AND_RESTORE.md`: recovery procedure.
- `RELEASE_CHECKLIST.md`: release approval checklist.

## Official references

- [GitHub OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [GitHub OIDC subject claims](https://docs.github.com/en/actions/reference/security/oidc)
- [GitHub Container Registry authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [AWS IAM OIDC role creation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)
- [AWS Systems Manager instance permissions](https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-permissions.html)
- [AWS Systems Manager Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html)
