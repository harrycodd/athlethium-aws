import json
import boto3
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
userTable = dynamodb.Table("userTable")
cognito_client = boto3.client('cognito-idp', region_name='eu-west-2')

def get_user_id_by_email(email, user_pool_id=None):
    try:
        if not user_pool_id:
            user_pool_id = os.environ.get('USER_POOL_ID')
        if not user_pool_id:
            return None
        response = cognito_client.list_users(
            UserPoolId=user_pool_id,
            Filter=f'email = "{email}"',
            Limit=1
        )
        if response.get('Users'):
            user = response['Users'][0]
            for attr in user.get('Attributes', []):
                if attr['Name'] == 'sub':
                    return attr['Value']
        return None
    except Exception as e:
        print(f"Error looking up user by email {email} in Cognito: {str(e)}")
        return None

def extract_user_id_from_cognito(event):
    try:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub')
        if not user_id:
            raise ValueError("userId (sub) not found in Cognito claims")
        return user_id
    except Exception as e:
        raise ValueError(f"Failed to extract userId from Cognito authentication: {str(e)}")

def lambda_handler(event, context):
    try:
        body = event.get('body')
        payload = json.loads(body) if isinstance(body, str) else event
    except Exception:
        payload = event
    try:
        http_method = payload.get("httpMethod")
        userId = extract_user_id_from_cognito(event)
        if http_method == "GET":
            return handle_get_request(userId)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def handle_get_request(userId):
    try:
        response = userTable.get_item(Key={"userId": userId})
        if "Item" in response:
            return {"statusCode": 200, "body": json.dumps(response["Item"], cls=DecimalEncoder)}
        else:
            return {"statusCode": 404, "body": json.dumps({"error": f"User with ID {userId} not found"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Server error: {str(e)}"})}