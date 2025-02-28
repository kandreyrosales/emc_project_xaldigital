import os
import json
import boto3
from boto3.dynamodb.conditions import Attr

# Inicializa el cliente DynamoDB
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "educational_data")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Filtrar solo los registros que corresponden a "especializacion"
        response = table.scan(
            FilterExpression=Attr("type").eq("especializacion")
        )

        # Formatear la respuesta
        specializations = [
            {
                "id": item["pk"],
                "nombre": item["nombre"]
            }
            for item in response.get("Items", [])
        ]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(specializations)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }