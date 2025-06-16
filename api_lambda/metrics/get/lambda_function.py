import json
import boto3
import os
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
dailyMetrics = dynamodb.Table("dailyMetrics")
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

def getTrainingMetrics(userId, date):
    try:
        current_date = datetime.strptime(date, "%Y-%m-%d")
        date_42_days_ago = (current_date - timedelta(days=42)).strftime("%Y-%m-%d")
        date_7_days_ago = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
        response_42_days = workoutsTable.scan(
            FilterExpression="userId = :uid AND #d BETWEEN :start_date AND :end_date AND completed = :completed",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={":uid": userId, ":start_date": date_42_days_ago, ":end_date": date, ":completed": True}
        )
        ctl_workouts = response_42_days.get("Items", [])
        ctl_sum = sum(float(workout.get("tss", 0)) for workout in ctl_workouts)
        ctl = round(ctl_sum / 42, 1)
        atl_workouts = [w for w in ctl_workouts if w.get("date") >= date_7_days_ago]
        atl_sum = sum(float(workout.get("tss", 0)) for workout in atl_workouts)
        atl = round(atl_sum / 7, 1)
        return {"ctl": ctl, "atl": atl}
    except Exception as e:
        return {"ctl": 0, "atl": 0}

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
        date = None
        if body:
            try:
                body_data = json.loads(body) if isinstance(body, str) else body
                date = body_data.get("date")
            except:
                pass
        if not date:
            return {"statusCode": 400, "body": json.dumps({"error": "date is required in request body"})}
        if http_method == "GET":
            return handle_get_request(userId, date)
        return {"statusCode": 405, "body": f"{http_method} does not exist"}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}

def handle_get_request(userId, date):
    try:
        user = userTable.get_item(Key={"userId": userId})
        if "Item" not in user:
            return {"statusCode": 404, "body": json.dumps({"error": f"User with ID {userId} not found"})}
        response = dailyMetrics.scan(
            FilterExpression="userId = :uid AND #d = :date",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={":uid": userId, ":date": date}
        )
        if "Items" in response and len(response["Items"]) > 0:
            item = response["Items"][0]
        else:
            item = {
                "metricId": str(uuid.uuid4()),
                "userId": userId,
                "date": date,
                "physicallyFeeling": "Average",
                "mentallyFeeling": "Average",
                "injury": "None",
                "illness": "None",
                "weight": 0,
                "dailyTrainingNotif": True,
                "uploadNotif": True
            }
            dailyMetrics.put_item(Item=item)
        training_metrics = getTrainingMetrics(userId, date)
        item.update(training_metrics)
        return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}, "body": json.dumps(item, cls=DecimalEncoder)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"Server error: {str(e)}"})}