resource "aws_dynamodb_table" "educational_data" {
  name         = "educational_data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi_relation"
    hash_key        = "relation_id"
    projection_type = "ALL"
  }

  attribute {
    name = "relation_id"
    type = "S"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "exams_data" {
  name         = "exams_data"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  global_secondary_index {
    name            = "gsi_exam"
    hash_key        = "curso_id"
    projection_type = "ALL"
  }

  attribute {
    name = "curso_id"
    type = "S"
  }

  tags = var.tags
}