import json
import boto3
import os
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr

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

def validate_date_range(start_date_str, end_date_str):
    """Validate date range and ensure it doesn't exceed 42 days"""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        date_diff = (end_date - start_date).days
        if date_diff > 42:
            raise ValueError("Date range cannot exceed 42 days")
        
        return start_date, end_date
    except ValueError as e:
        if "time data" in str(e):
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise e

def get_metrics_for_date_range(userId, start_date_str, end_date_str):
    """Get metrics for a date range"""
    try:
        start_date, end_date = validate_date_range(start_date_str, end_date_str)
        
        response = dailyMetrics.scan(
            FilterExpression=Attr("userId").eq(userId) & Attr("date").between(start_date_str, end_date_str)
        )
        
        metrics_items = response.get("Items", [])
        
        # Sort by date
        metrics_items.sort(key=lambda x: x.get("date", ""))
        
        # Add training metrics for each date
        for item in metrics_items:
            date = item.get("date")
            if date:
                training_metrics = getTrainingMetrics(userId, date)
                item.update(training_metrics)
        
        return metrics_items
    except Exception as e:
        raise Exception(f"Error retrieving metrics for date range: {str(e)}")

def get_metrics_for_single_date(userId, date):
    """Get metrics for a single date"""
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        response = dailyMetrics.scan(
            FilterExpression=Attr("userId").eq(userId) & Attr("date").eq(date)
        )
        
        if "Items" in response and len(response["Items"]) > 0:
            item = response["Items"][0]
        else:
            # Create default metrics if none exist
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
        
        # Add training metrics
        training_metrics = getTrainingMetrics(userId, date)
        item.update(training_metrics)
        
        return [item]  # Return as array for consistency
    except ValueError as e:
        if "time data" in str(e):
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise e

def lambda_handler(event, context):
    try:
        userId = extract_user_id_from_cognito(event)
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Check if user exists
        user = userTable.get_item(Key={"userId": userId})
        if "Item" not in user:
            return {
                "statusCode": 404, 
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": f"User with ID {userId} not found"})
            }
        
        try:
            # Handle different query parameter combinations
            date = query_params.get('date')
            start_date = query_params.get('startDate')
            end_date = query_params.get('endDate')
            
            metrics_data = []
            
            if date:
                # Single date query
                metrics_data = get_metrics_for_single_date(userId, date)
            elif start_date and end_date:
                # Date range query
                metrics_data = get_metrics_for_date_range(userId, start_date, end_date)
            elif start_date or end_date:
                # Invalid - both start and end dates required for range
                return {
                    "statusCode": 400,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"error": "Both startDate and endDate are required for date range queries"})
                }
            else:
                # No query parameters - return error (we don't want to return all metrics)
                return {
                    "statusCode": 400,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({
                        "error": "Query parameters required. Use 'date' for single date or 'startDate' and 'endDate' for date range"
                    })
                }
            
            return {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "userId": userId,
                    "metrics": metrics_data
                }, cls=DecimalEncoder)
            }
            
        except ValueError as ve:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": str(ve)})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": f"Server error: {str(e)}"})
            }
            
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": f"Authentication error: {str(e)}"})
        }