import json
import boto3
import os
import uuid

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
workoutsTable = dynamodb.Table("workoutsTable")
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
        http_method = event.get("httpMethod")
        userId = extract_user_id_from_cognito(event)
        date = None
        workoutId = None
        if body:
            try:
                body_data = json.loads(body) if isinstance(body, str) else body
                date = body_data.get("date")
                workoutId = body_data.get("workoutId")
            except:
                pass
        if http_method == "POST":
            if not body:
                return {"statusCode": 400, "body": json.dumps("Content of body is empty")}
            if not date:
                return {"statusCode": 400, "body": json.dumps({"error": "date is required in request body"})}
            return handle_post_request(userId, date, body)
        if http_method == "PUT":
            if not body:
                return {"statusCode": 400, "body": json.dumps("Content of body is empty")}
            if not workoutId:
                return {"statusCode": 400, "body": json.dumps({"error": "workoutId is required in request body"})}
            return handle_put_request(workoutId, body)
        return {"statusCode": 405, "body": json.dumps(f"{http_method} does not exist")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def handle_post_request(user_id, date, body):
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            return {"statusCode": 400, "body": json.dumps("Error! Body is not valid JSON!")}
    if isinstance(body, list):
        if len(body) == 0:
            return {"statusCode": 400, "body": json.dumps("Error! Body list is empty!")}
        body = body[0]
    if not user_id or not date:
        return {"statusCode": 400, "body": json.dumps("Missing userId or date in request body")}
    workoutId = str(uuid.uuid4())
    item = {"workoutId": workoutId, "userId": user_id, "date": date}
    if not isinstance(body, dict):
        return {"statusCode": 400, "body": json.dumps("Error! Body is not a JSON object!")}
    for key, value in body.items():
        item[key] = value
    if 'session_focus' not in item:
        item['session_focus'] = body.get('session_focus', None)
    try:
        workoutsTable.put_item(Item=item)
        return {"statusCode": 201, "body": json.dumps({"message": f"Success! Created new record for workoutId {workoutId}!", "workoutId": workoutId})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {e}")}

def handle_put_request(workoutId, body):
    if type(body) == str:
        try:
            body = json.loads(body)
        except Exception:
            return {"statusCode": 400, "body": json.dumps("Error! Body is not valid JSON!")}
    try:
        rsp = workoutsTable.get_item(Key={"workoutId": workoutId})
        if "Item" in rsp:
            item = rsp["Item"]
            for key, value in body.items():
                item[key] = value
            if 'userId' not in item and 'userId' in body:
                item['userId'] = body['userId']
            if 'date' not in item and 'date' in body:
                item['date'] = body['date']
            if 'session_focus' not in item:
                item['session_focus'] = body.get('session_focus', None)
            workoutsTable.put_item(Item=item)
            return {"statusCode": 200, "body": json.dumps(f"Success! Updated the record for workoutId {workoutId}!")}
        else:
            user_id = body.get('userId')
            date = body.get('date')
            item = {"workoutId": workoutId}
            if user_id:
                item['userId'] = user_id
            if date:
                item['date'] = date
            for key, value in body.items():
                item[key] = value
            if 'session_focus' not in item:
                item['session_focus'] = body.get('session_focus', None)
            workoutsTable.put_item(Item=item)
            return {"statusCode": 201, "body": json.dumps(f"Success! Created new record for workoutId {workoutId}!")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {e}")}


