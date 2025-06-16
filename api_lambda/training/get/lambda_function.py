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
workoutsTable = dynamodb.Table("workoutsTable")
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
    user_id = (
        event.get('userId') or
        (event.get('pathParameters', {}) or {}).get('userId') or
        (event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')) or
        (event.get('requestContext', {}).get('identity', {}).get('user')) or
        (event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('cognito:username'))
    )
    if not user_id:
        raise ValueError("userId could not be extracted from event")
    if '@' in str(user_id):
        actual_user_id = get_user_id_by_email(user_id, os.environ.get('USER_POOL_ID'))
        if actual_user_id:
            return actual_user_id
        else:
            raise ValueError(f"Could not find userId for email: {user_id}")
    return user_id

def lambda_handler(event, context):
    try:
        body = event.get('body')
        payload = json.loads(body) if isinstance(body, str) else event
    except Exception:
        payload = event
    try:
        http_method = payload.get("httpMethod")
        userId = extract_user_id_from_cognito(event)
        date = None
        if body:
            try:
                body_data = json.loads(body) if isinstance(body, str) else body
                date = body_data.get("date")
            except:
                pass
        if http_method == "GET":
            return handle_get_request(userId, date)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def handle_get_request(userId, date):
    try:
        user = userTable.get_item(Key={"userId": userId})
        if "Item" not in user:
            return {"statusCode": 404, "body": json.dumps({"error": f"User with user ID {userId} not found"})}
        response = workoutsTable.scan(
            FilterExpression="userId = :uid AND #d = :date",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={":uid": userId, ":date": date}
        )
        if "Items" in response and len(response["Items"]) > 0:
            return {"statusCode": 200, "body": json.dumps(response["Items"], cls=DecimalEncoder)}
        return {"statusCode": 200, "body": json.dumps([])}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Server error: {str(e)}"})}


