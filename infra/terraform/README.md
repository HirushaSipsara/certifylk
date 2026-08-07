# CertifyLK Terraform deployment

This Terraform root automates AWS and GitHub connection work for the CertifyLK production Compose deployment. It is product-agnostic: Track 1/Track 2 catalogue and workflow changes use the same immutable-image pipeline and require no Terraform redesign.

## Current applied environment

Terraform has been applied successfully for the recorded single-host deployment:

| Output | Verified value |
|---|---|
| Public URL | <https://certifylk.duckdns.org> |
| Region | `ap-south-1` |
| Elastic IP | `3.108.242.97` |
| EC2 instance | `i-00e924bf43a9d1fbe` |
| GitHub role | `arn:aws:iam::622215957056:role/certifylk-github-deploy` |

The initial apply created 15 resources. Subsequent applies updated the GitHub immutable OIDC trust and attached the exact customer-managed Systems Manager deployment policy. The current Terraform plan is clean, and GitHub CI plus production deployment passed for commit `77cd9cbbf6bc42533bfa87e9c2ebf0692a0d577d`.

## Automated resources

- dedicated VPC, internet gateway, public subnet, and route table;
- security group exposing only HTTP 80 and HTTPS 443;
- encrypted Ubuntu x86_64 EC2 instance and Elastic IP;
- EC2 Systems Manager instance role/profile;
- GitHub Actions OIDC provider, trust policy, and least-privilege SSM deployment role;
- optional Route 53 A record;
- optional USD monthly budget alerts;
- optional GitHub `production` environment and its four non-secret variables;
- EC2 cloud-init installation of Docker, Certbot, Git, directories, public repository clone, mock-mode production environment, generated PostgreSQL password, and certificate request after DNS points to the instance.

## Deliberately not stored in Terraform

Terraform state can expose values supplied to managed resources. Therefore Terraform does not accept or manage:

- PostgreSQL passwords;
- Gemini API keys;
- private GHCR tokens;
- private GitHub deploy keys;
- TLS private keys.

The PostgreSQL password is generated on EC2 at first boot. Gemini and private GHCR credentials are added directly to protected EC2 files only when required. Never put them in `terraform.tfvars`.

## Prerequisites

1. The repository is pushed to GitHub and its CI succeeds.
2. Terraform 1.10 or newer is installed.
3. AWS CLI v2 is authenticated to the intended account. This guide uses a dedicated IAM user and named AWS CLI profile for the initial Terraform run.
4. A real hostname is available. A free DuckDNS subdomain is sufficient for a temporary deployment; purchasing a domain is not required.
5. For automated GitHub environment variables, a GitHub token with permission to administer the repository environment/actions variables is available only in the current Terraform process.

## 1. Authenticate locally to AWS

This is the familiar local flow:

```text
IAM user -> access key -> aws configure -> named profile -> Terraform
```

Never create access keys for the AWS root user. Create or select a dedicated IAM user such as `certifylk-terraform`, enable MFA for its console access when applicable, and create an access key for the **Command Line Interface (CLI)** use case.

The user must have permission to create the resources listed in this document, including VPC, EC2, EBS, Elastic IP, IAM roles/policies, Systems Manager integration, and the optional Route 53 and Budgets resources. For a personal first-time bootstrap, attaching AWS managed `AdministratorAccess` temporarily is the simplest option but is broad. Remove that policy and deactivate or delete the access key after provisioning, or replace it with a reviewed least-privilege provisioning policy.

Configure the credentials in a named local profile:

```powershell
aws configure --profile certifylk-terraform
```

Enter the values when prompted:

```text
AWS Access Key ID:     value from the IAM user
AWS Secret Access Key: value shown once when the key is created
Default region name:   ap-south-1
Default output format: json
```

AWS CLI saves that named profile under your Windows user profile, outside this repository. Select it for the current PowerShell session and verify the identity before running Terraform:

```powershell
$env:AWS_PROFILE = "certifylk-terraform"
aws configure list --profile certifylk-terraform
aws sts get-caller-identity --profile certifylk-terraform
```

Confirm that the returned account ID and ARN are the intended IAM user. Terraform's AWS provider automatically uses the selected AWS CLI profile.

Do not put `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` in `terraform.tfvars`, Terraform provider blocks, GitHub variables/secrets, workflow YAML, or any repository file. These credentials are only for the local Terraform run. GitHub Actions uses the separate OIDC role created by Terraform and does not need this IAM user's access key.

### Optional SSO alternative

If you later prefer temporary AWS IAM Identity Center credentials, the equivalent setup is:

```powershell
aws configure sso
aws sso login --profile YOUR_SSO_PROFILE
$env:AWS_PROFILE = "YOUR_SSO_PROFILE"
aws sts get-caller-identity --profile YOUR_SSO_PROFILE
```

## 2. Optionally authenticate Terraform to GitHub

Skip this section and keep `manage_github_environment=false` if you prefer to copy four Terraform outputs into GitHub manually.

For automation, create a short-lived/fine-grained repository token able to administer environments and Actions variables. Load it into the current PowerShell process without saving it in a file or command history:

```powershell
$githubTokenSecure = Read-Host "GitHub token" -AsSecureString
$env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new("", $githubTokenSecure).Password
```

Set `manage_github_environment=true` in `terraform.tfvars`. Clear the environment variable after Terraform finishes:

```powershell
Remove-Item Env:GITHUB_TOKEN
```

The token is provider authentication and is not declared as a Terraform input or resource value.

## 3. Configure non-secret inputs

### Free temporary hostname when you do not own a domain

Create a free DuckDNS subdomain before running Terraform:

1. Sign in at [DuckDNS](https://www.duckdns.org/).
2. Register an available, unique name such as `certifylk-yourname`.
3. Your Terraform hostname will be `certifylk-yourname.duckdns.org`.

Do not use the example name unless you successfully registered it. Do not put the DuckDNS token in Terraform or GitHub; after the Elastic IP is created, update the address manually in the DuckDNS dashboard.

```powershell
Set-Location F:\Projects\certifylk\infra\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

At minimum, replace:

```hcl
domain_name  = "certifylk-yourname.duckdns.org"
tls_email   = "your-real-email@example.org"
budget_email = "your-real-email@example.org"
```

For DuckDNS, keep:

```hcl
route53_zone_id = null
```

When DNS is in Route 53, set its existing public hosted-zone ID:

```hcl
route53_zone_id = "Z0123456789EXAMPLE"
```

When DNS is hosted elsewhere, keep `route53_zone_id = null`. Terraform outputs the Elastic IP to enter in the external provider.

If the AWS account already has the GitHub OIDC provider, set:

```hcl
existing_github_oidc_provider_arn = "arn:aws:iam::AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
```

This repository uses GitHub's immutable OIDC subject format. The owner and repository IDs are non-secret identifiers configured as `github_owner_id` and `github_repository_id`, producing this exact trusted subject:

```text
repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production
```

If the repository is transferred or this Terraform root is reused, obtain the new immutable IDs from the GitHub repository API or the rejected subject in AWS CloudTrail and update both variables before applying.

For a private repository set:

```hcl
repository_is_public = false
```

Cloud-init will then skip cloning. Add the read-only deploy key and clone after apply using `docs/AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md`.

## 4. Initialize, format, validate, and review

```powershell
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
```

Review every planned resource. Expected chargeable resources are one EC2 instance, one gp3 volume, and one public IPv4 address. Route 53 and budget resources appear only when configured.

Do not apply if Terraform proposes an unexpected instance type, additional instance, NAT Gateway, load balancer, RDS database, or destructive replacement.

## 5. Apply

```powershell
terraform apply
```

Type `yes` only after reviewing the final plan.

Show connection outputs afterward:

```powershell
terraform output
terraform output -json github_environment_variables
```

When `manage_github_environment=false`, copy the four output values to:

```text
GitHub repository -> Settings -> Environments -> production -> Environment variables
```

The variables are:

```text
AWS_REGION
AWS_ROLE_ARN
EC2_INSTANCE_ID
PRODUCTION_DOMAIN
```

No AWS access keys are required in GitHub.

## 6. Finish DNS when it is external

When `route53_zone_id=null`, create this record at the DNS provider:

```text
Type: A
Name: the selected subdomain
Value: terraform output -raw elastic_ip
TTL: 300
```

For the temporary DuckDNS option:

```powershell
$elasticIp = terraform output -raw elastic_ip
Write-Output $elasticIp
```

Open the DuckDNS dashboard, enter that Elastic IP beside your registered subdomain, and choose **update ip**. Verify it before continuing:

```powershell
Resolve-DnsName certifylk-yourname.duckdns.org
```

The returned IPv4 address must equal `$elasticIp`. The EC2 bootstrap waits for this match before requesting the HTTPS certificate.

Cloud-init checks that the hostname resolves to its Elastic IP before calling Certbot. This avoids repeated invalid certificate requests while DNS is incomplete.

## 7. Watch EC2 bootstrap

Open **AWS Systems Manager -> Session Manager**, connect to the Terraform-created instance, then run:

```bash
sudo cloud-init status --wait
sudo tail -n 200 /var/log/cloud-init-output.log
```

Do not share the full log if it unexpectedly contains sensitive data.

Expected results for a public repository:

```text
/opt/certifylk/repository/.git
/opt/certifylk/repository/infra/production/.env.production
/etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem
```

Verify file protection without printing its contents:

```bash
sudo stat -c '%a %U:%G %n' /opt/certifylk/repository/infra/production/.env.production
```

Expected mode/owner: `600 certifylk:certifylk`.

If cloud-init reports an error because the repository was private when the instance started, changing repository visibility does not automatically rerun the failed clone step. Follow the repository recovery guidance under Troubleshooting, confirm the protected environment file exists, and then deploy through the normal GitHub workflow. Do not destroy the instance just to retry bootstrap.

## 8. Configure private GHCR only when required

If application packages are private, add the read-only package token directly on EC2:

```bash
sudo -H -u certifylk editor /opt/certifylk/repository/infra/production/.env.registry
sudo -H -u certifylk chmod 600 /opt/certifylk/repository/infra/production/.env.registry
```

```env
GHCR_USERNAME=your-github-user
GHCR_TOKEN=your_read_packages_only_token
```

Do not put this token in Terraform or GitHub Actions secrets. Public packages need no registry file.

## 9. Trigger the application deployment

The existing GitHub workflow deploys only after a successful `CI` push run on `main`. If the earlier first deployment failed before Terraform finished, open **GitHub -> Actions -> Deploy production** and choose **Re-run all jobs**.

The deployment must:

1. publish both images using the tested full commit SHA;
2. authenticate to AWS through the Terraform-created OIDC role;
3. send the SHA to the Terraform-created EC2 instance through SSM;
4. back up, migrate, seed, start, and health-check the Compose stack.

## 10. Verify and enable Gemini later

```powershell
$domain = terraform output -raw public_url
Invoke-RestMethod "$domain/api/v1/health"
Invoke-RestMethod "$domain/api/v1/ready"
Start-Process $domain
```

Complete the sample workflow in mock mode first. Then add `GEMINI_API_KEY` only to EC2 `infra/production/.env.production` and redeploy. The key never enters Terraform state.

## State safety

Local Terraform state is gitignored but still controls real infrastructure. Back it up to protected encrypted storage. Do not email it, paste it into issues, or commit it.

For a team or long-lived production system, migrate to an encrypted remote backend with access control and state locking before multiple operators run Terraform. Do not hardcode backend credentials.

Commit `.terraform.lock.hcl` after `terraform init`; it records reviewed provider selections. Do not commit:

```text
.terraform/
terraform.tfstate
terraform.tfstate.backup
terraform.tfvars
*.tfplan
```

## Safe teardown

`terraform destroy` is destructive and removes the instance, EBS data, Elastic IP, network, IAM roles, DNS record managed by this root, and GitHub environment managed by this root.

Before permanent teardown:

1. export and verify the final database/upload backup;
2. confirm the correct AWS profile, account ID, region, and Terraform state;
3. run `terraform plan -destroy` and review every target;
4. only then run `terraform destroy`.

Do not use destroy for a temporary pause. Stop the EC2 instance instead, remembering that EBS and IPv4-related charges may continue.

## Troubleshooting

### OIDC provider already exists

Set `existing_github_oidc_provider_arn` to its exact ARN and apply again. Do not create a duplicate provider.

### `Not authorized to perform sts:AssumeRoleWithWebIdentity`

Inspect the rejected event in AWS CloudTrail and compare its full principal subject with the IAM role trust policy. New GitHub repositories use immutable owner and repository IDs in the `repo` segment. Confirm `github_owner_id`, `github_repository_id`, and `github_environment`, then run `terraform plan` and `terraform apply` to update the role in place. Do not weaken the subject to a wildcard.

### Terraform cannot configure GitHub

Set `manage_github_environment=false`, apply AWS resources, and copy `github_environment_variables` manually. This does not affect AWS infrastructure.

### Certificate is missing

Confirm the domain resolves to `elastic_ip`, security-group port 80 is open, and cloud-init completed. Then follow the Certbot command in `docs/AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md`.

### Repository is private

Cloud-init intentionally does not accept a GitHub private key or token through Terraform. Configure the read-only EC2 deploy key, clone, and create `.env.production` using the focused deployment guide.

If the first clone failed and the repository was subsequently made public, connect through Session Manager and clone as the service user into the expected path. Preserve the Terraform-created directories and ownership:

```bash
sudo test ! -e /opt/certifylk/repository/.git
sudo -H -u certifylk git clone https://github.com/HirushaSipsara/certifylk.git /opt/certifylk/repository
sudo chown -R certifylk:certifylk /opt/certifylk
```

Then create `.env.production` on the host using `docs/PRODUCTION_DEPLOYMENT.md`. Generate its PostgreSQL password on EC2, set mock AI mode for the first public verification, and protect it with mode `600`; never print the file or copy its secret through Terraform.

### GitHub environment variable validation fails

Remove leading/trailing spaces from `AWS_REGION`, `AWS_ROLE_ARN`, `EC2_INSTANCE_ID`, and `PRODUCTION_DOMAIN`. The current workflow normalizes them defensively and validates the normalized outputs before AWS authentication.

### SSM reports `Illegal option -o pipefail`

`AWS-RunShellScript` executes its command list with `/bin/sh`. The workflow wrapper must use portable `set -eu`. It should invoke `infra/production/scripts/deploy.sh` explicitly with `bash`; do not remove Bash strict mode from that script.

### `.env.production` is missing

Recreate it only on EC2 from `infra/production/.env.production.example`. Generate a new URL-safe PostgreSQL password on the host, use it consistently in `POSTGRES_PASSWORD` and `DATABASE_URL`, start in mock mode, and set `600 certifylk:certifylk`. Do not use Terraform, GitHub variables, workflow logs, or SSM command parameters to transport the secret.

### Terraform proposes replacing EC2

Stop and review the cause. Back up production data before approving any instance replacement. Persistent application volumes currently live on that single EC2 host.

## Official references

- [Terraform AWS getting started](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
- [AWS CLI configuration and named profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [AWS access-key security guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/securing_access-keys.html)
- [AWS root-user security guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html)
- [DuckDNS free dynamic DNS and update behavior](https://www.duckdns.org/faqs.jsp)
- [Terraform sensitive data and state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)
- [Terraform state guidance](https://developer.hashicorp.com/terraform/language/state)
- [AWS OIDC federation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc.html)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
