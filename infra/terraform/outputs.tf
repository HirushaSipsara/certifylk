output "instance_id" {
  description = "EC2 instance targeted by GitHub deployment."
  value       = aws_instance.app.id
}

output "elastic_ip" {
  description = "Elastic IP for the DNS A record."
  value       = aws_eip.app.public_ip
}

output "public_url" {
  description = "Expected CertifyLK public URL after DNS and certificate bootstrap."
  value       = "https://${var.domain_name}"
}

output "github_deploy_role_arn" {
  description = "AWS role ARN used by GitHub OIDC."
  value       = aws_iam_role.github_deploy.arn
}

output "github_environment_variables" {
  description = "Non-secret values to add to the GitHub production environment when manage_github_environment is false."
  value       = local.github_environment_values
}

output "route53_managed" {
  description = "Whether Terraform created the domain A record in Route 53."
  value       = var.route53_zone_id != null
}

output "next_steps" {
  description = "Operator steps that intentionally remain outside Terraform state."
  value = [
    var.repository_is_public ? "Wait for EC2 cloud-init to clone the public repository and create .env.production in mock mode." : "Configure the private repository deploy key and clone into /opt/certifylk/repository.",
    var.route53_zone_id != null ? "Wait for DNS and cloud-init certificate issuance." : "Create an A record for ${var.domain_name} pointing to ${aws_eip.app.public_ip}; cloud-init will issue the certificate after DNS matches.",
    var.manage_github_environment ? "GitHub production environment variables were managed by Terraform." : "Copy the github_environment_variables output into the GitHub production environment.",
    "For private GHCR packages, create EC2 infra/production/.env.registry with a read:packages token.",
    "Rerun Deploy production after cloud-init, DNS, certificate, repository, and GHCR access are ready.",
    "Add GEMINI_API_KEY only to EC2 infra/production/.env.production after the mock-mode public sample passes.",
  ]
}

