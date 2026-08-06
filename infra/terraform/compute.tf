data "aws_ssm_parameter" "ubuntu_amd64" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

locals {
  cloud_init = templatefile("${path.module}/user_data.sh.tftpl", {
    domain_name          = var.domain_name
    tls_email            = var.tls_email
    ghcr_owner           = var.ghcr_owner
    repository_clone_url = var.repository_clone_url
    repository_is_public = var.repository_is_public
  })
}

resource "aws_instance" "app" {
  ami                         = data.aws_ssm_parameter.ubuntu_amd64.value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  associate_public_ip_address = true
  user_data                   = local.cloud_init
  user_data_replace_on_change = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = var.root_volume_size_gb
  }

  tags = {
    Name = "certifylk-${var.environment}"
  }

  depends_on = [aws_route_table_association.public]
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id

  tags = {
    Name = "certifylk-${var.environment}"
  }
}

