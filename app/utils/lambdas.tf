# Define IAM role for Lambda function

# Define Lambda function confirm Email
resource "aws_lambda_function" "confirm_email_emc" {
  function_name    = "confirm_email_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "confirm_email.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}
resource "aws_lambda_function_url" "lambda_url_confirm_email_emc" {
  function_name = aws_lambda_function.confirm_email_emc.arn
  authorization_type = "NONE"
}

# Define Lambda function resend Code
resource "aws_lambda_function" "resend_code_emc" {
  function_name    = "resend_code_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "resend_code.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}
resource "aws_lambda_function_url" "lambda_url_resend_code_emc" {
  function_name = aws_lambda_function.resend_code_emc.arn
  authorization_type = "NONE"
}

# Define Lambda function Forgot Password
resource "aws_lambda_function" "forgot_password_emc" {
  function_name    = "forgot_password_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "forgot_password.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}
resource "aws_lambda_function_url" "lambda_url_forgot_password_emc" {
  function_name = aws_lambda_function.forgot_password_emc.arn
  authorization_type = "NONE"
}

# Define Lambda function Confirm Forgot Password
resource "aws_lambda_function" "confirm_forgot_password_emc" {
  function_name    = "confirm_forgot_password_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "confirm_forgot_password.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}
resource "aws_lambda_function_url" "lambda_url_confirm_forgot_password_emc" {
  function_name = aws_lambda_function.confirm_forgot_password_emc.arn
  authorization_type = "NONE"
}

# Define Lambda function GetUserInfo
resource "aws_lambda_function" "get_user_info_emc" {
  function_name    = "get_user_info_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "get_user_info.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}
resource "aws_lambda_function_url" "lambda_url_get_user_info_emc" {
  function_name = aws_lambda_function.get_user_info_emc.arn
  authorization_type = "NONE"
}

# Define Lambda function Logout
resource "aws_lambda_function" "logout_emc" {
  function_name    = "logout_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "logout.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}
resource "aws_lambda_function_url" "lambda_url_logout_emc" {
  function_name = aws_lambda_function.logout_emc.arn
  authorization_type = "NONE"
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

# Agregar permisos para DynamoDB Scan
resource "aws_iam_policy" "lambda_dynamodb_policy_emc" {
  name        = "lambda_dynamodb_policy"
  description = "IAM policy for Lambda to access DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = "arn:aws:dynamodb:${var.region_aws}:${var.aws_account_number}:table/educational_data"
      }
    ]
  })
}

# Asociar la política a la IAM Role de la Lambda
resource "aws_iam_role_policy_attachment" "lambda_dynamodb_attach_emc" {
  role       = aws_iam_role.lambda_role_emc.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy_emc.arn
}

# Add CloudWatch Logs permission to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_logs_emc" {
  role       = aws_iam_role.lambda_role_emc.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Add Cognito permissions to Lambda role
resource "aws_iam_role_policy" "lambda_cognito_policy_emc" {
  name = "lambda_cognito_policy_emc"
  role = aws_iam_role.lambda_role_emc.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:SignUp",
          "cognito-idp:ConfirmSignUp",
          "cognito-idp:ForgotPassword",
          "cognito-idp:ConfirmForgotPassword",
          "cognito-idp:ResendConfirmationCode",
          "cognito-idp:AdminGetUser"
        ]
        Resource = [aws_cognito_user_pool.emc_user_pool.arn]
      }
    ]
  })
}

# Create ZIP archive of Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../lambdas/"
  output_path = "${path.module}/lambda_function.zip"
}

# Define Lambda function SignUp
resource "aws_lambda_function" "signup_emc" {
  function_name    = "signup_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "signup.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId     = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}

# Define Lambda function SignIn
resource "aws_lambda_function" "signin_emc" {
  function_name    = "signin_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "signin.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      clientId     = aws_cognito_user_pool_client.mobile_emc_client.id
      clientSecret = aws_cognito_user_pool_client.mobile_emc_client.client_secret
      CORS_ALLOW_ORIGIN = var.cors_allow_origin
    }
  }
}

resource "aws_lambda_function" "specializations_emc" {
  function_name    = "specializations_emc"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "specializations.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.educational_data.name
    }
  }
}

variable "cors_allow_origin" {
  description = "CORS allowed origins"
  type        = string
  default     = "*"  # For development. In production, specify exact domains
}

# Outputs
output "lambda_function_urls" {
  description = "URLs for Lambda functions"
  value = {
    signup = "${aws_api_gateway_stage.api_stage_emc.invoke_url}/signup"
    signin = "${aws_api_gateway_stage.api_stage_emc.invoke_url}/signin"
    specializations = "${aws_api_gateway_stage.api_stage_emc.invoke_url}/specializations"
    # Add other function URLs as needed
  }
}
