variable "aws_region" {
  description = "AWS region for every CertifyLK resource."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name used in AWS tags and GitHub OIDC trust."
  type        = string
  default     = "production"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, digits, and hyphens."
  }
}

variable "domain_name" {
  description = "Public CertifyLK hostname, without a scheme."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9.-]+$", var.domain_name)) && !endswith(var.domain_name, "example.com")
    error_message = "domain_name must be a real DNS hostname and not an example.com placeholder."
  }
}

variable "tls_email" {
  description = "Email address used by Certbot for certificate notices."
  type        = string

  validation {
    condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.tls_email))
    error_message = "tls_email must be a valid email address."
  }
}

variable "github_owner" {
  description = "Case-sensitive GitHub repository owner used in the OIDC subject."
  type        = string
  default     = "HirushaSipsara"
}

variable "github_repository" {
  description = "GitHub repository name without its owner."
  type        = string
  default     = "certifylk"
}

variable "ghcr_owner" {
  description = "Lowercase GHCR image owner."
  type        = string
  default     = "hirushasipsara"

  validation {
    condition     = var.ghcr_owner == lower(var.ghcr_owner) && can(regex("^[a-z0-9][a-z0-9._-]*$", var.ghcr_owner))
    error_message = "ghcr_owner must be lowercase and registry-safe."
  }
}

variable "repository_clone_url" {
  description = "Public HTTPS clone URL used by EC2 cloud-init. Private repositories must be cloned with a deploy key after apply."
  type        = string
  default     = "https://github.com/HirushaSipsara/certifylk.git"
}

variable "repository_is_public" {
  description = "Whether cloud-init may clone the repository without a deploy key."
  type        = bool
  default     = true
}

variable "github_environment" {
  description = "GitHub environment trusted by AWS OIDC."
  type        = string
  default     = "production"
}

variable "manage_github_environment" {
  description = "Create the GitHub environment and its four non-secret variables. Requires GITHUB_TOKEN in the Terraform process."
  type        = bool
  default     = false
}

variable "existing_github_oidc_provider_arn" {
  description = "Existing token.actions.githubusercontent.com IAM provider ARN. Leave null to create it."
  type        = string
  default     = null
  nullable    = true
}

variable "instance_type" {
  description = "EC2 instance type. t3.small is the credit-conscious demonstration default."
  type        = string
  default     = "t3.small"
}

variable "root_volume_size_gb" {
  description = "Encrypted gp3 root volume size."
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_size_gb >= 20
    error_message = "root_volume_size_gb must be at least 20 GiB."
  }
}

variable "vpc_cidr" {
  description = "CIDR for the dedicated CertifyLK VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR for the single public application subnet."
  type        = string
  default     = "10.42.1.0/24"
}

variable "route53_zone_id" {
  description = "Optional existing public Route 53 hosted-zone ID. Leave null when DNS is managed elsewhere."
  type        = string
  default     = null
  nullable    = true
}

variable "budget_email" {
  description = "Email for the monthly AWS budget alert. Leave empty to skip budget creation."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly AWS cost budget in USD."
  type        = number
  default     = 25

  validation {
    condition     = var.monthly_budget_usd > 0
    error_message = "monthly_budget_usd must be greater than zero."
  }
}

