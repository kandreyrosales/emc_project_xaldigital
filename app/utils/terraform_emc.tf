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

resource "aws_cognito_user_pool_client" "emc_cognito_client" {
  name = "emc_cognito_client"
  user_pool_id = aws_cognito_user_pool.emc_user_pool.id
  # Configure other settings as needed
  explicit_auth_flows = ["ADMIN_NO_SRP_AUTH", "USER_PASSWORD_AUTH"]
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