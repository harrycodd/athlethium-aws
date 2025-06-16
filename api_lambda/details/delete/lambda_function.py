import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
userTable = dynamodb.Table("userTable")

def lambda_handler(event, context):
    try:
        body = event.get('body')
        payload = json.loads(body) if isinstance(body, str) else event
    except Exception:
        payload = event

    # Handle Cognito user deletion trigger
    if "triggerSource" in payload:
        if payload["triggerSource"].startswith("PreTokenGeneration_"):
            return handle_cognito_deletion(payload, context)
        # Always return the event for Cognito triggers
        return payload

def handle_cognito_deletion(event, context):
    try:
        # Get the user ID from the Cognito event
        user_id = event["request"]["userAttributes"]["sub"]
        print(f"Handling deletion for Cognito user: {user_id}")
        
        # Delete the user data
        userTable.delete_item(Key={"userId": user_id})
        print(f"Successfully deleted user data for {user_id}")
        
        # Important: always return the event for Cognito triggers
        return event
    
    except Exception as e:
        print(f"Error handling Cognito user deletion: {str(e)}")
        # Even on error, return the event (don't block the Cognito process)
        raise e