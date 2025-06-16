import json
import boto3
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

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
        http_method = payload.get("httpMethod")
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
        if http_method == "GET":
            return handle_get_request(workoutId)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def handle_get_request(workoutId):
    try:
        response = workoutsTable.get_item(Key={"workoutId": workoutId})
        if "Item" not in response:
            return {"statusCode": 404, "body": json.dumps({"error": f"Workout with workoutId {workoutId} not found"})}
        return {"statusCode": 200, "body": json.dumps(response["Item"], cls=DecimalEncoder)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Server error: {str(e)}"})}


