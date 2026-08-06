# CertifyLK Terraform deployment

This Terraform root automates the repetitive AWS and GitHub connection work for the existing CertifyLK production Compose deployment.

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
3. AWS CLI v2 is authenticated to the intended account using temporary credentials, preferably IAM Identity Center/SSO.
4. A real domain or subdomain is available.
5. For automated GitHub environment variables, a GitHub token with permission to administer the repository environment/actions variables is available only in the current Terraform process.

## 1. Authenticate locally to AWS

Do not create root access keys and do not put AWS keys in GitHub.

Configure an AWS SSO profile once:

```powershell
aws configure sso
```

Start the session and select it for Terraform:

```powershell
aws sso login --profile YOUR_PROFILE
$env:AWS_PROFILE = "YOUR_PROFILE"
aws sts get-caller-identity
```

Confirm the returned account ID before applying.

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

```powershell
Set-Location F:\Projects\certifylk\infra\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

At minimum, replace:

```hcl
domain_name = "app.your-real-domain.lk"
tls_email   = "your-real-email@example.org"
budget_email = "your-real-email@example.org"
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

### Terraform cannot configure GitHub

Set `manage_github_environment=false`, apply AWS resources, and copy `github_environment_variables` manually. This does not affect AWS infrastructure.

### Certificate is missing

Confirm the domain resolves to `elastic_ip`, security-group port 80 is open, and cloud-init completed. Then follow the Certbot command in `docs/AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md`.

### Repository is private

Cloud-init intentionally does not accept a GitHub private key or token through Terraform. Configure the read-only EC2 deploy key, clone, and create `.env.production` using the focused deployment guide.

### Terraform proposes replacing EC2

Stop and review the cause. Back up production data before approving any instance replacement. Persistent application volumes currently live on that single EC2 host.

## Official references

- [Terraform AWS getting started](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
- [Terraform sensitive data and state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)
- [Terraform state guidance](https://developer.hashicorp.com/terraform/language/state)
- [AWS OIDC federation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc.html)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)

