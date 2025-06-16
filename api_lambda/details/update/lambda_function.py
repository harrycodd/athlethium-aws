import json
import boto3
import os

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
    if 'triggerSource' in event:
        return PostConfirmation(event, context)
    try:
        http_method = event.get("httpMethod")
        userId = extract_user_id_from_cognito(event)
        if http_method == "PUT":
            body = event.get("body")
            if not body:
                return {"statusCode": 400, "body": json.dumps("Content of body is empty")}
            return handle_put_request(userId, body)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def PostConfirmation(event, context):
    user_attributes = event["request"]["userAttributes"]
    user_id = user_attributes.get("sub")
    try:
        cognito = boto3.client("cognito-idp")
        user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
        if user_pool_id and user_id:
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=user_id,
                UserAttributes=[{"Name": "email_verified", "Value": "true"}]
            )
    except Exception as e:
        print(f"Failed to auto-confirm email for {user_id}: {e}")
    userTable.put_item(Item={"userId": user_id, "signUpCompleted": False})
    return event

def handle_put_request(userId, body):
    if type(body) == str:
        try:
            body = json.loads(body)
        except Exception:
            return {"statusCode": 400, "body": json.dumps("Error! Body is not valid JSON!")}
    try:
        rsp = userTable.get_item(Key={"userId": userId})
        if "Item" in rsp:
            item = rsp["Item"]
            for key, value in body.items():
                item[key] = value
            userTable.put_item(Item=item)
            return {"statusCode": 200, "body": json.dumps(f"Success! Updated the record for user-id {userId}!")}
        else:
            return {"statusCode": 404, "body": json.dumps(f"userId:{userId} not found!")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {e}")}


