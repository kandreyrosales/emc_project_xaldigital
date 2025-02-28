provider "aws" {
  region = var.region_aws
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

resource "aws_cognito_user_pool" "emc_user_pool" {
  name = var.cognito_pool_name
  # Enable admin user password authentication
  username_attributes = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
  }

  schema {
    attribute_data_type = "String"
    name                = "fullname"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "medical_specialty"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "professional_id"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "residence_age"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "hospital"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "doctor_name"
    required            = false
    mutable             = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }
}

resource "aws_cognito_user_pool_client" "mobile_emc_client" {
  name = "mobile_emc_client"
  user_pool_id = aws_cognito_user_pool.emc_user_pool.id
  # Configure other settings as needed
  explicit_auth_flows = ["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_PASSWORD_AUTH"]
  enable_token_revocation = true
  prevent_user_existence_errors = "ENABLED"
  generate_secret = true
}

resource "aws_iam_policy" "cognito_list_emc_users_policy" {
  name        = "cognito-list-emc-users-policy"
  description = "Allows Lambda execution role to list users in Cognito User Pool"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "cognito-idp:ListUsers"
        Resource = "arn:aws:cognito-idp:${var.region_aws}:${var.aws_account_number}:userpool/${aws_cognito_user_pool.emc_user_pool.id}"
      },
      {
        "Action": [
           "logs:CreateLogGroup",
           "logs:CreateLogStream",
           "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:*",
        "Effect": "Allow"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cognito_list_users_emc_policy_attachment" {
  role       = aws_iam_role.lambda_role_emc.name
  policy_arn = aws_iam_policy.cognito_list_emc_users_policy.arn
}

# Attach IAM policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_emc_attachment" {
  role       = aws_iam_role.lambda_role_emc.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"  # Attach a read-only S3 access policy
}

