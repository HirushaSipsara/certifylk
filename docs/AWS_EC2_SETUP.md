# AWS EC2 setup

This runbook provisions and operates infrastructure only. It is reusable for the Track 1/Track 2 redesign and does not validate certification content or scheme-specific domain behavior. Use `RELEASE_CHECKLIST.md` for current product smoke gates.

For the complete first-time sequence—including billing safeguards, GitHub/GHCR, DNS, TLS, OIDC, SSM, first deployment, and verification—follow `AWS_GITHUB_DEPLOYMENT_GUIDE.md`. This document remains the focused EC2 reference.

## Target

Use one supported Ubuntu LTS EC2 instance with an encrypted EBS root volume and enough CPU, memory, and disk for the frontend, backend, PostgreSQL, image layers, uploads, and backups. The credit-conscious synthetic-data demonstration may start on x86_64 `t3.small` with 30 GiB gp3 and close monitoring. A practical real-traffic baseline is at least 2 vCPU, 4 GiB RAM, and 40 GiB gp3; measure the workload before changing capacity.

Allocate an Elastic IP. Create DNS A (and AAAA only if IPv6 is fully configured) records for the production domain. The security group allows inbound TCP 80 and 443 from the internet. Do not expose 3000, 5432, or 8000. Prefer Systems Manager Session Manager over public SSH; if port 22 is temporarily required, restrict it to a known administrator IP and remove it afterward.

## Instance IAM role and SSM

Attach an instance profile containing the AWS-managed `AmazonSSMManagedInstanceCore` policy. Ubuntu AWS AMIs normally include SSM Agent, but verify it:

```bash
sudo systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service || \
sudo systemctl status amazon-ssm-agent.service
```

In Systems Manager Fleet Manager, confirm the instance is online before configuring GitHub.

## Host installation

Install Docker Engine and Compose from Docker’s official Ubuntu apt repository, not the convenience script. Follow the current Docker instructions, then verify:

```bash
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

Install Git, curl, Certbot, and operational tools:

```bash
sudo apt update
sudo apt install -y git curl certbot jq ca-certificates
```

Create the dedicated operator and protected directories:

```bash
sudo adduser --system --group --home /opt/certifylk certifylk
sudo usermod -aG docker certifylk
sudo install -d -o certifylk -g certifylk -m 750 /opt/certifylk/repository
sudo install -d -o certifylk -g certifylk -m 700 /var/lib/certifylk/releases /var/backups/certifylk
sudo install -d -o root -g root -m 755 /var/www/certbot
```

Membership in the Docker group is effectively host-level privilege. Do not use this account for interactive application users.

Clone the repository as `certifylk`:

```bash
sudo -H -u certifylk git clone https://github.com/HirushaSipsara/certifylk.git /opt/certifylk/repository
```

If the repository is private, configure a read-only GitHub deploy key for that repository instead of embedding a token in the clone URL. Verify `git fetch --prune origin` works non-interactively as `certifylk`.

Complete the production environment and certificate steps in `PRODUCTION_DEPLOYMENT.md`.

## GitHub OIDC provider and role

Create an IAM OIDC identity provider with:

- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

Create a role named `certifylk-github-deploy`. Its trust policy must match the exact repository/environment subject produced by GitHub. For repositories using the traditional subject format:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
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
  }]
}
```

Newer repositories may use immutable owner/repository IDs in `sub`. Inspect GitHub’s OIDC subject format for this repository and use that exact value. Never use a repository-wide wildcard.

Attach this narrow customer-managed permissions policy after replacing region, account ID, and instance ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UseApprovedRunShellDocument",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ssm:AWS_REGION::document/AWS-RunShellScript"
    },
    {
      "Sid": "SendCommandToExactCertifyLKInstance",
      "Effect": "Allow",
      "Action": "ssm:SendCommand",
      "Resource": "arn:aws:ec2:AWS_REGION:AWS_ACCOUNT_ID:instance/EC2_INSTANCE_ID"
    },
    {
      "Sid": "ReadAndCancelOwnCommand",
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

Add the resulting role ARN and EC2 coordinates to the GitHub `production` environment as described in `CI_CD.md`.

## Host hardening and maintenance

- Enable automatic security updates and schedule reboots when kernel updates require them.
- Use EBS encryption, IMDSv2-only instance metadata, and least-privilege IAM roles.
- Use CloudWatch or another approved log/metric destination if operational monitoring is later authorized; the application currently logs to container stdout/stderr.
- Monitor disk use under `/var/lib/docker`, the PostgreSQL volume, upload volume, and `/var/backups/certifylk`.
- Patch the OS and Docker deliberately, after a backup and release review.
- Snapshot encrypted EBS in addition to application-level backups when the retention policy requires it.
