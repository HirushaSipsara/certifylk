resource "github_repository_environment" "production" {
  count = var.manage_github_environment ? 1 : 0

  repository  = var.github_repository
  environment = var.github_environment
}

locals {
  github_environment_values = {
    AWS_REGION        = var.aws_region
    AWS_ROLE_ARN      = aws_iam_role.github_deploy.arn
    EC2_INSTANCE_ID   = aws_instance.app.id
    PRODUCTION_DOMAIN = var.domain_name
  }
}

resource "github_actions_environment_variable" "production" {
  for_each = var.manage_github_environment ? local.github_environment_values : {}

  repository    = var.github_repository
  environment   = github_repository_environment.production[0].environment
  variable_name = each.key
  value         = each.value
}

