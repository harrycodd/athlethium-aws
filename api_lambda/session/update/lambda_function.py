import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
workoutsTable = dynamodb.Table("workoutsTable")

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
        http_method = event.get("httpMethod")
        userId = extract_user_id_from_cognito(event)
        workoutId = None
        if body:
            try:
                body_data = json.loads(body) if isinstance(body, str) else body
                workoutId = body_data.get("workoutId")
            except:
                pass
        if not workoutId:
            return {"statusCode": 400, "body": json.dumps({"error": "workoutId is required in request body"})}
        if http_method == "PUT":
            body_content = event.get("body")
            if not body_content:
                return {"statusCode": 400, "body": json.dumps("Content of body is empty")}
            return handle_put_request(workoutId, body_content)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

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
            if 'session_focus' not in item:
                item['session_focus'] = body.get('session_focus', None)
            workoutsTable.put_item(Item=item)
            lambda_client = boto3.client('lambda')
            user_id = body.get('userId')
            if user_id:
                try:
                    lambda_client.invoke(
                        FunctionName='training_algorithm',
                        InvocationType='Event',
                        Payload=json.dumps({'userId': user_id})
                    )
                except Exception as e:
                    print(f"Error invoking training_algorithm Lambda: {e}")
            return {"statusCode": 200, "body": json.dumps(f"Success! Updated the record for workoutId {workoutId}!")}
        else:
            return {"statusCode": 404, "body": json.dumps(f"workoutId:{workoutId} not found!")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {e}")}


