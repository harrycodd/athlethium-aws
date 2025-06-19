import json
import datetime
import boto3
from decimal import Decimal
from training_algorithm import training_algorithm

def lambda_handler(event, context):
    """
    Individual training algorithm Lambda function
    Called for specific users and dates
    """
    try:
        # Parse the request body
        if 'httpMethod' in event:
            # API Gateway request
            body = json.loads(event['body']) if event.get('body') else {}
        else:
            # Direct invocation
            body = event
        
        user_id = body.get('userId')
        date_str = body.get('date')
        
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'userId is required'})
            }
        
        # Parse date or use today
        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid date format. Use YYYY-MM-DD'})
                }
        else:
            target_date = datetime.date.today()
        
        # Get user profile (simplified version for individual calls)
        user_profile = get_user_profile_simple(user_id, target_date)
        
        if not user_profile:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found or incomplete profile'})
            }
        
        # Run the training algorithm
        result = training_algorithm(user_profile, target_date, user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Training session generated successfully',
                'userId': user_id,
                'date': date_str or target_date.strftime('%Y-%m-%d')
            })
        }
        
    except Exception as e:
        print(f"Error in training algorithm lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_user_profile_simple(user_id: str, current_date: datetime.date):
    """
    Simplified user profile getter for individual calls
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name="eu-west-2")
        userTable = dynamodb.Table("userTable")
        
        # Get user data
        user_response = userTable.get_item(Key={'userId': user_id})
        if 'Item' not in user_response:
            return None
        
        user_data = user_response['Item']
        
        # Build basic profile (simplified for individual calls)
        user_profile = {
            'weekly_hours': float(user_data.get('weekly_hours', 10)),
            'intensity_weeks': int(user_data.get('intensity_weeks', 3)),
            'interval_type': user_data.get('interval_type', 'structured'),
            'recovery_metric': int(user_data.get('recovery_metric', 3)),
            'sports': user_data.get('sports', ['cycling', 'running']),
            'focused_sports': user_data.get('focused_sports', ['cycling']),
            'injury': int(user_data.get('injury', 0)),
            'illness': int(user_data.get('illness', 0)),
            'ctl': float(user_data.get('ctl', 50)),
            'atl': float(user_data.get('atl', 40)),
            'goal': user_data.get('goal', {}),
            'event': user_data.get('event', {}),
            'upcoming_schedule': [float(user_data.get('daily_available_hours', 2))] * 7,
            'schedule': [float(user_data.get('daily_available_hours', 2))] * 7,
            'history': {
                'cycling': {'focus': [-1] * 7, 'hours': [0] * 7},
                'running': {'focus': [-1] * 7, 'hours': [0] * 7},
                'swimming': {'focus': [-1] * 7, 'hours': [0] * 7},
                'strength': {'focus': [-1] * 7, 'hours': [0] * 7}
            },
            'sessions': []
        }
        
        return user_profile
        
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None