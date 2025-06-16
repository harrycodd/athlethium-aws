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
        if http_method == "DELETE":
            try:
                workoutsTable.delete_item(Key={"workoutId": workoutId})
                lambda_client = boto3.client('lambda')
                try:
                    lambda_client.invoke(
                        FunctionName='training_algorithm',
                        InvocationType='Event',
                        Payload=json.dumps({'userId': userId})
                    )
                except Exception as e:
                    print(f"Error invoking training_algorithm Lambda: {e}")
                return {"statusCode": 200, "body": json.dumps(f"Successfully deleted workoutId {workoutId}")}
            except Exception as e:
                return {"statusCode": 500, "body": json.dumps(f"Error deleting workout: {str(e)}")}
        return {"statusCode": 405, "body": json.dumps(f"Method {http_method} not allowed")}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
