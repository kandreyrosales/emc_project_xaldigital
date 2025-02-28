# api_gateway.tf
resource "aws_api_gateway_rest_api" "emc_api" {
  name = "emc_api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# Enable CORS
resource "aws_api_gateway_resource" "cors_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "{proxy+}"
}

# OPTIONS method for CORS
resource "aws_api_gateway_method" "options_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.cors_emc.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# CORS Integration
resource "aws_api_gateway_integration" "options_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.cors_emc.id
  http_method = aws_api_gateway_method.options_emc.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# CORS Method Response
resource "aws_api_gateway_method_response" "options_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.cors_emc.id
  http_method = aws_api_gateway_method.options_emc.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# CORS Integration Response
resource "aws_api_gateway_integration_response" "options_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.cors_emc.id
  http_method = aws_api_gateway_method.options_emc.http_method
  status_code = aws_api_gateway_method_response.options_emc.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# API Resources and Methods for your endpoints for signin
resource "aws_api_gateway_resource" "signin_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "signin"
}

# Example POST method for signin
resource "aws_api_gateway_method" "signin_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.signin_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "signin_integration_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.signin_emc.id
  http_method = aws_api_gateway_method.signin_post_emc.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.signin_emc.invoke_arn

  integration_http_method = "POST"
}

# Method Response
resource "aws_api_gateway_method_response" "signin_response_200_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.signin_emc.id
  http_method = aws_api_gateway_method.signin_post_emc.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}


resource "aws_api_gateway_resource" "get_specializations_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "specializations"
}

resource "aws_api_gateway_method" "get_specializations_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.get_specializations_emc.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_specializations_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.get_specializations_emc.id
  http_method             = aws_api_gateway_method.get_specializations_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.specializations_emc.invoke_arn
  integration_http_method = "POST"
}

# Integration Response
resource "aws_api_gateway_integration_response" "signin_integration_response_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.signin_emc.id
  http_method = aws_api_gateway_method.signin_post_emc.http_method
  status_code = aws_api_gateway_method_response.signin_response_200_emc.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_integration.signin_integration_emc
  ]
}

# Deployment and Stage
resource "aws_api_gateway_deployment" "api_deployment_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id

  depends_on = [
    aws_api_gateway_integration.options_emc,
    aws_api_gateway_integration.signin_integration_emc,
    aws_api_gateway_integration.signup_integration_emc,
    aws_api_gateway_integration.confirm_email_integration_emc,
    aws_api_gateway_integration.resend_code_emc_integration_emc,
    aws_api_gateway_integration.forgot_password_emc_integration_emc,
    aws_api_gateway_integration.confirm_forgot_password_emc_integration_emc,
    aws_api_gateway_integration.get_user_info_emc_integration_emc,
    aws_api_gateway_integration.logout_emc_integration_emc
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api_stage_emc" {
  deployment_id = aws_api_gateway_deployment.api_deployment_emc.id
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  stage_name    = var.environment
}

# Enable CORS for the stage
resource "aws_api_gateway_method_settings" "api_settings_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  stage_name  = aws_api_gateway_stage.api_stage_emc.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

# Outputs
output "api_url" {
  description = "API Gateway URL"
  value       = "${aws_api_gateway_stage.api_stage_emc.invoke_url}"
}

# Add CloudWatch logging
resource "aws_api_gateway_account" "api_gateway_account_emc" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_emc.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch_emc" {
  name = "api_gateway_cloudwatch_role_emc"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "api_gateway_cloudwatch_emc" {
  name = "api_gateway_cloudwatch_policy_emc"
  role = aws_iam_role.api_gateway_cloudwatch_emc.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_signup_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signup_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_signin_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signin_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Lambda permissions for API Gateway specializations_emc
resource "aws_lambda_permission" "api_gateway_get_specializations_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.specializations_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Recurso para signup en API Gateway
resource "aws_api_gateway_resource" "signup_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "signup"
}

# Método POST para signup
resource "aws_api_gateway_method" "signup_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.signup_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para signup
resource "aws_api_gateway_integration" "signup_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.signup_emc.id
  http_method             = aws_api_gateway_method.signup_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.signup_emc.invoke_arn
  integration_http_method = "POST"
}

# Configuración de la respuesta en API Gateway
resource "aws_api_gateway_method_response" "signup_response_200_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.signup_emc.id
  http_method = aws_api_gateway_method.signup_post_emc.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# Integración de respuesta para permitir CORS
resource "aws_api_gateway_integration_response" "signup_integration_response_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.signup_emc.id
  http_method = aws_api_gateway_method.signup_post_emc.http_method
  status_code = aws_api_gateway_method_response.signup_response_200_emc.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_integration.signup_integration_emc
  ]
}


# Recurso API Gateway para confirmar email
resource "aws_api_gateway_resource" "confirm_email_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "confirm-email"
}

# Método POST para confirmar email
resource "aws_api_gateway_method" "confirm_email_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.confirm_email_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para confirmar email
resource "aws_api_gateway_integration" "confirm_email_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.confirm_email_emc.id
  http_method             = aws_api_gateway_method.confirm_email_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.confirm_email_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda confirm_email
resource "aws_lambda_permission" "api_gateway_confirm_email_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.confirm_email_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Resend Code
# Recurso API Gateway para Resend Code
resource "aws_api_gateway_resource" "resend_code_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "resend_code"
}

# Método POST para Resend Code
resource "aws_api_gateway_method" "resend_code_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.resend_code_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para Resend Code
resource "aws_api_gateway_integration" "resend_code_emc_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.resend_code_emc.id
  http_method             = aws_api_gateway_method.resend_code_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.resend_code_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda Resend Code
resource "aws_lambda_permission" "api_gateway_resend_code_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.resend_code_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Forgot Password
# Recurso API Gateway para forgot_password
resource "aws_api_gateway_resource" "forgot_password_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "forgot_password"
}

# Método POST para forgot_password
resource "aws_api_gateway_method" "forgot_password_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.forgot_password_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para forgot_password
resource "aws_api_gateway_integration" "forgot_password_emc_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.forgot_password_emc.id
  http_method             = aws_api_gateway_method.forgot_password_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.forgot_password_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda forgot_password
resource "aws_lambda_permission" "api_gateway_forgot_password_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.forgot_password_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Get User Info
# Recurso API Gateway para get_user_info
resource "aws_api_gateway_resource" "get_user_info_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "get_user_info"
}

# Método POST para get_user_info
resource "aws_api_gateway_method" "get_user_info_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.get_user_info_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para get_user_info
resource "aws_api_gateway_integration" "get_user_info_emc_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.get_user_info_emc.id
  http_method             = aws_api_gateway_method.get_user_info_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_user_info_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda get_user_info
resource "aws_lambda_permission" "api_gateway_get_user_info_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_user_info_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Logout
# Recurso API Gateway para logout
resource "aws_api_gateway_resource" "logout_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "logout"
}

# Método POST para logout
resource "aws_api_gateway_method" "logout_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.logout_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para logout
resource "aws_api_gateway_integration" "logout_emc_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.logout_emc.id
  http_method             = aws_api_gateway_method.logout_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.logout_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda logout
resource "aws_lambda_permission" "api_gateway_logout_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.logout_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

# Confirm Forgot Password
# Recurso API Gateway para confirm_forgot_password
resource "aws_api_gateway_resource" "confirm_forgot_password_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id   = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part   = "confirm_password_change"
}

# Método POST para confirm_forgot_password
resource "aws_api_gateway_method" "confirm_forgot_password_post_emc" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.confirm_forgot_password_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integración con Lambda para confirm_forgot_password
resource "aws_api_gateway_integration" "confirm_forgot_password_emc_integration_emc" {
  rest_api_id             = aws_api_gateway_rest_api.emc_api.id
  resource_id             = aws_api_gateway_resource.confirm_forgot_password_emc.id
  http_method             = aws_api_gateway_method.confirm_forgot_password_post_emc.http_method
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.confirm_forgot_password_emc.invoke_arn
  integration_http_method = "POST"
}

# Permiso para API Gateway sobre la Lambda confirm_forgot_password
resource "aws_lambda_permission" "api_gateway_confirm_forgot_password_emc" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.confirm_forgot_password_emc.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}
