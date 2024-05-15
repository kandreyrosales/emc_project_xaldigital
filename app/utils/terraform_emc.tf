provider "aws" {
  region = var.region_aws
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
    attribute_data_type = "Number"
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


# Define IAM role for Lambda function
resource "aws_iam_role" "lambda_role_emc" {
  name = "lambda_role_emc"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
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

# Create ZIP archive of Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../lambdas/"  # Path to the directory containing Lambda function code
  output_path = "${path.module}/lambda_function.zip"
}

# Define Lambda function SignUp
resource "aws_lambda_function" "signup" {
  function_name    = "signup"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "signup.lambda_handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
    }
  }
}

# Define Lambda function SignIn
resource "aws_lambda_function" "signin" {
  function_name    = "signin"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "lambda-insights.lambda_handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
    }
  }
}