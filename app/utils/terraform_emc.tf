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

resource "aws_security_group" "rds_sg_emc" {
  name_prefix = "rds_sg_emc"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"   // Allow all protocols
    cidr_blocks     = ["0.0.0.0/0"]  // Allow traffic to any IPv4 address
  }
}

### POSTRESQL RDS

resource "aws_db_instance" "posgtres_rds_emc" {
  engine                 = "postgres"
  db_name                = var.db_name
  identifier             = "emc"
  instance_class         = "db.t3.micro"
  engine_version         = "12"
  allocated_storage      = 20
  publicly_accessible    = true
  username               = var.db_username
  password               = var.db_password
  vpc_security_group_ids = [aws_security_group.rds_sg_emc.id]
  skip_final_snapshot    = true

  tags = {
    Name = "emc-db"
  }
}

output "endpoint" {
  value = aws_db_instance.posgtres_rds_emc.endpoint
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
  handler          = "signup.handler"
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
resource "aws_lambda_function_url" "lambda_url_signup" {
  function_name = aws_lambda_function.signup.arn
  authorization_type = "NONE"
}



# Define Lambda function SignIn
resource "aws_lambda_function" "signin" {
  function_name    = "signin"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "signin.handler"
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
resource "aws_lambda_function_url" "lambda_url_signin" {
  function_name = aws_lambda_function.signin.arn
  authorization_type = "NONE"
}

# Define Lambda function confirm Email
resource "aws_lambda_function" "confirm_email" {
  function_name    = "confirm_email"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "confirm_email.handler"
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
resource "aws_lambda_function_url" "lambda_url_confirm_email" {
  function_name = aws_lambda_function.confirm_email.arn
  authorization_type = "NONE"
}

# Define Lambda function resend Code
resource "aws_lambda_function" "resend_code" {
  function_name    = "resend_code"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "resend_code.handler"
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
resource "aws_lambda_function_url" "lambda_url_resend_code" {
  function_name = aws_lambda_function.resend_code.arn
  authorization_type = "NONE"
}

# Define Lambda function Forgot Password
resource "aws_lambda_function" "forgot_password" {
  function_name    = "forgot_password"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "forgot_password.handler"
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
resource "aws_lambda_function_url" "lambda_url_forgot_password" {
  function_name = aws_lambda_function.forgot_password.arn
  authorization_type = "NONE"
}

# Define Lambda function Confirm Forgot Password
resource "aws_lambda_function" "confirm_forgot_password" {
  function_name    = "confirm_forgot_password"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "confirm_forgot_password.handler"
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
resource "aws_lambda_function_url" "lambda_url_confirm_forgot_password" {
  function_name = aws_lambda_function.confirm_forgot_password.arn
  authorization_type = "NONE"
}

# Define Lambda function GetUserInfo
resource "aws_lambda_function" "get_user_info" {
  function_name    = "get_user_info"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "get_user_info.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}
resource "aws_lambda_function_url" "lambda_url_get_user_info" {
  function_name = aws_lambda_function.get_user_info.arn
  authorization_type = "NONE"
}

# Define Lambda function Logout
resource "aws_lambda_function" "logout" {
  function_name    = "logout"
  role             = aws_iam_role.lambda_role_emc.arn
  handler          = "logout.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}
resource "aws_lambda_function_url" "lambda_url_logout" {
  function_name = aws_lambda_function.logout.arn
  authorization_type = "NONE"
}

####### API EMC #######
resource "aws_api_gateway_rest_api" "emc_api" {
  name = "emc_api"

  endpoint_configuration {
    types = ["REGIONAL"] # Exposes the API publicly
  }
}

### API LOGIN ####
resource "aws_api_gateway_resource" "api_resource_emc_login" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "login" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_login" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_emc_login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_login" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signin.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_login" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_emc_login.id
  http_method = aws_api_gateway_method.api_method_login.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.signin.invoke_arn
  integration_http_method = "POST"
}

####### API SIGNUP #########
resource "aws_api_gateway_resource" "api_resource_signup_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "signup" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_signup" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_signup_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_signup" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signup.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_signup" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_signup_emc.id
  http_method = aws_api_gateway_method.api_method_signup.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.signup.invoke_arn
  integration_http_method = "POST"
}
########

# #### API LOGOUT #####
resource "aws_api_gateway_resource" "api_resource_logout_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "logout" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_logout" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_logout_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_logout" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.logout.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_logout" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_logout_emc.id
  http_method = aws_api_gateway_method.api_method_logout.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.logout.invoke_arn
  integration_http_method = "POST"
}
#######
#### API CONFIRM EMAIL #####
resource "aws_api_gateway_resource" "api_resource_confirm_email_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "confirm_email" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_confirm_email" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_confirm_email_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_confirm_email" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.confirm_email.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_confirm_email" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_confirm_email_emc.id
  http_method = aws_api_gateway_method.api_method_confirm_email.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.confirm_email.invoke_arn
  integration_http_method = "POST"
}
########
#### API FORGOT PASSWORD #####
resource "aws_api_gateway_resource" "api_resource_forgot_password_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "forgot_password" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_forgot_password" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_forgot_password_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_forgot_password" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.forgot_password.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_forgot_password" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_forgot_password_emc.id
  http_method = aws_api_gateway_method.api_method_forgot_password.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.forgot_password.invoke_arn
  integration_http_method = "POST"
}
########
#### API CONFIRM FORGOT PASSWORD #####
resource "aws_api_gateway_resource" "api_resource_confirm_forgot_password_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "confirm_forgot_password" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_confirm_forgot_password" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_confirm_forgot_password_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_confirm_forgot_password" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.confirm_forgot_password.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_confirm_forgot_password" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_confirm_forgot_password_emc.id
  http_method = aws_api_gateway_method.api_method_confirm_forgot_password.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.confirm_forgot_password.invoke_arn
  integration_http_method = "POST"
}
########
#### API RESEND CODE #####
resource "aws_api_gateway_resource" "api_resource_resend_code_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "resend_code" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_resend_code" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_resend_code_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_resend_code" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.resend_code.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_resend_code" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_resend_code_emc.id
  http_method = aws_api_gateway_method.api_method_resend_code.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.resend_code.invoke_arn
  integration_http_method = "POST"
}
########
#### API GET USER INFORMATION #####
resource "aws_api_gateway_resource" "api_resource_get_user_info_emc" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  parent_id    = aws_api_gateway_rest_api.emc_api.root_resource_id
  path_part    = "get_user_info" # Replace with your desired path

  depends_on = [aws_api_gateway_rest_api.emc_api]
}

resource "aws_api_gateway_method" "api_method_get_user_info" {
  rest_api_id   = aws_api_gateway_rest_api.emc_api.id
  resource_id   = aws_api_gateway_resource.api_resource_get_user_info_emc.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "api_gateway_permission_get_user_info" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_user_info.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.emc_api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda_integration_get_user_info" {
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  resource_id = aws_api_gateway_resource.api_resource_get_user_info_emc.id
  http_method = aws_api_gateway_method.api_method_get_user_info.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.get_user_info.invoke_arn
  integration_http_method = "POST"
}
########


resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
      aws_api_gateway_method.api_method_login,
      aws_api_gateway_integration.lambda_integration_login,
      aws_api_gateway_method.api_method_signup,
      aws_api_gateway_integration.lambda_integration_signup,
      aws_api_gateway_method.api_method_logout,
      aws_api_gateway_integration.lambda_integration_logout,

      aws_api_gateway_method.api_method_confirm_email,
      aws_api_gateway_integration.lambda_integration_confirm_email,

      aws_api_gateway_method.api_method_confirm_forgot_password,
      aws_api_gateway_integration.lambda_integration_confirm_forgot_password,

      aws_api_gateway_method.api_method_get_user_info,
      aws_api_gateway_integration.lambda_integration_get_user_info,

      aws_api_gateway_method.api_method_resend_code,
      aws_api_gateway_integration.lambda_integration_resend_code,

      aws_api_gateway_method.api_method_forgot_password,
      aws_api_gateway_integration.lambda_integration_forgot_password

  ]
  rest_api_id = aws_api_gateway_rest_api.emc_api.id
  stage_name  = "prod"
}

output "api_url" {
  value = "${aws_api_gateway_deployment.api_deployment.invoke_url}"
}

resource "aws_instance" "flask_ec2_emc" {
  ami                    = var.ami
  instance_type          = var.instance_type
  key_name               = var.ssh_key_pair_name
  associate_public_ip_address = true


  provisioner "remote-exec" {
    inline = [
      # Install required packages
      "sudo apt-get update -y",
      "sudo apt-get install -y python3 git",
      "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py",
      "sudo python3 get-pip.py",
      "sudo apt-get install -y python3-venv",  # Install python3-venv package for virtual environments
      "sudo apt-get install -y libpq-dev python3-dev",


      "echo \"export db_endpoint=${aws_db_instance.posgtres_rds_emc.endpoint}\" >> ~/.bashrc",
      "echo \"export db_password=${var.db_password}\" >> ~/.bashrc",

      # Clone Flask application from GitHub
      "git clone https://github.com/kandreyrosales/emc_project_xaldigital.git /home/ubuntu/flask_app",


      # Create and activate virtual environment
      "cd /home/ubuntu/flask_app",
      "python3 -m venv venv",
      "source venv/bin/activate",
      "cd app/",

      # Install dependencies
      "pip install -r requirements.txt",

      "sudo ufw allow 5000",

      # Create a systemd service for Gunicorn
      "cat <<EOF | sudo tee /etc/systemd/system/flask_app.service",
      "[Unit]",
      "Description=Gunicorn instance to serve Flask application",
      "After=network.target",

      "[Service]",
      "User=ubuntu",
      "Group=ubuntu",
      "WorkingDirectory=/home/ubuntu/flask_app/app",
      "Environment=\"PATH=/home/ubuntu/flask_app/venv/bin\"",
      "ExecStart=/home/ubuntu/.local/bin/gunicorn -w 1 -b 0.0.0.0:5000 -e bucket_name=${var.bucket_name} -e region_aws=${var.region_aws} -e accessKeyId=${var.accessKeyId} -e secretAccessKey=${var.secretAccessKey} -e db_endpoint=${aws_db_instance.posgtres_rds_emc.endpoint} -e db_name=${var.db_name} -e db_username=${var.db_username} -e db_password=${var.db_password} app:app",
      "Restart=always",

      "[Install]",
      "WantedBy=multi-user.target",
      "EOF",

      # Start and enable the Gunicorn service
      "sudo systemctl daemon-reload",
      "sudo systemctl start flask_app",
      "sudo systemctl enable flask_app",
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"  # SSH username for Amazon Linux, CentOS, or Red Hat AMIs
      private_key = file(var.private_key_ec2_path)  # Replace with the path to your SSH private key file
      host        = self.public_ip
    }
  }

  tags = {
    Name = "EMC-Flask-Ubuntu"
  }

  vpc_security_group_ids = [aws_security_group.flask_sg_emc.id]

}

resource "aws_security_group" "flask_sg_emc" {
  name        = "flask_sg_emc"
  description = "Security group for Flask EC2 EMC project instance"

  // Ingress rule to allow HTTP traffic from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  // Allow traffic from any IPv4 address
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"   // Allow all protocols
    cidr_blocks     = ["0.0.0.0/0"]  // Allow traffic to any IPv4 address
  }
}

output "public_ip" {
  value = aws_instance.flask_ec2_emc.public_ip
}

