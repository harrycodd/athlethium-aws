import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from training_algorithm import TrainingAlgorithm
import uuid

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def to_dynamodb_decimals(obj):
    if isinstance(obj, list):
        return [to_dynamodb_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: to_dynamodb_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, float) or (isinstance(obj, int) and not isinstance(obj, bool)):
        return Decimal(str(obj))
    else:
        return obj

dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
dailyMetrics = dynamodb.Table("dailyMetrics")
userTable = dynamodb.Table("userTable")
workoutsTable = dynamodb.Table("workoutsTable")
trainingSchedule = dynamodb.Table("trainingSchedule")

SPORTS = ["cycling", "running", "swimming", "strength", "yoga"]

def get_ctl_atl(userId, date):
    current_date = datetime.strptime(date, "%Y-%m-%d")
    date_42_days_ago = (current_date - timedelta(days=42)).strftime("%Y-%m-%d")
    date_7_days_ago = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
    response_42_days = workoutsTable.scan(
        FilterExpression="userId = :uid AND #d BETWEEN :start_date AND :end_date AND completed = :completed",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":start_date": date_42_days_ago,
            ":end_date": date,
            ":completed": True
        }
    )
    ctl_workouts = convert_decimals(response_42_days.get("Items", []))
    ctl_workouts = [w if isinstance(w, dict) else {} for w in ctl_workouts]
    ctl_sum = sum(float(w.get("tss", 0)) for w in ctl_workouts)
    ctl = round(ctl_sum / 42, 1)
    atl_workouts = [w for w in ctl_workouts if isinstance(w, dict) and w.get("date") >= date_7_days_ago]
    atl_sum = sum(float(w.get("tss", 0)) for w in atl_workouts)
    atl = round(atl_sum / 7, 1)
    return ctl, atl

def get_metrics_for_sport(userId, date, sport):
    # Get daily metrics for a sport on a given day
    response = dailyMetrics.scan(
        FilterExpression="userId = :uid AND #d = :date AND sport = :sport",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":date": date,
            ":sport": sport
        }
    )
    if response.get("Items"):
        return convert_decimals(response["Items"][0])
    return {}

def get_hours_and_focus(userId, date, sport):
    # Sum up hours and get focus for a sport on a given day from workoutsTable
    response = workoutsTable.scan(
        FilterExpression="userId = :uid AND #d = :date AND sport = :sport AND completed = :completed",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":date": date,
            ":sport": sport,
            ":completed": True
        }
    )
    items = convert_decimals(response.get("Items", []))
    items = [w if isinstance(w, dict) else {} for w in items]
    hours = sum(float(w.get("time", 0)) for w in items)
    focus = items[0].get("focus", -1) if items and isinstance(items[0], dict) else -1
    return hours, focus

def get_last_7_days_history(userId, date):
    history = {}
    for sport in SPORTS:
        ctl, atl = get_ctl_atl(userId, date)
        hours_list = []
        focus_list = []
        for i in range(7):
            d = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=i)).strftime("%Y-%m-%d")
            hours, focus = get_hours_and_focus(userId, d, sport)
            # Ensure hours and focus are always numbers
            if isinstance(hours, (list, dict)):
                hours = 0
            if isinstance(focus, (list, dict)):
                focus = -1
            if not isinstance(hours, (int, float)):
                try:
                    hours = float(hours)
                except Exception:
                    hours = 0
            if not isinstance(focus, (int, float)):
                try:
                    focus = float(focus)
                except Exception:
                    focus = -1
            hours_list.append(hours)
            focus_list.append(focus)
        history[sport] = {
            "ctl": ctl,
            "atl": atl,
            "hours": hours_list[::-1],
            "focus": focus_list[::-1]
        }
    return history

def get_upcoming_schedule(userId, date):
    response = trainingSchedule.scan(
        FilterExpression="userId = :uid AND #d = :date",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":date": date
        }
    )
    if response.get("Items"):
        item = convert_decimals(response["Items"][0])
        hours = item.get("avaliableHours", 0)
        # Always return a scalar (int or float)
        if isinstance(hours, list):
            return hours[0] if hours else 0
        if not isinstance(hours, (int, float)):
            try:
                hours = float(hours)
            except Exception:
                hours = 0
        return hours
    user = userTable.get_item(Key={"userId": userId})
    if "Item" in user:
        user_item = convert_decimals(user["Item"])
        day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday()
        default_sched = user_item.get("defaultSchedule", [0]*7)
        if isinstance(default_sched, list) and len(default_sched) > day_of_week:
            return default_sched[day_of_week]
        elif isinstance(default_sched, int):
            return default_sched
    return 0

def get_goals_events_sessions(userId, date):
    # Get future, incomplete goals/events/sessions from workoutsTable
    response = workoutsTable.scan(
        FilterExpression="userId = :uid AND #d >= :date AND completed = :false",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":date": date,
            ":false": False
        }
    )
    items = convert_decimals(response.get("Items", []))
    items = [w if isinstance(w, dict) else {} for w in items]
    goals = [w for w in items if w.get("event_type") == "goal"]
    events = [w for w in items if w.get("event_type") == "event"]
    sessions = [w for w in items if w.get("event_type") == "training"]
    return goals, events, sessions

def get_user_profile_fields(userId, date):
    # Fetch userTable fields
    user = userTable.get_item(Key={"userId": userId})
    user_fields = user.get("Item", {})
    user_fields = convert_decimals(user_fields)
    # Fetch metrics for the day
    response = dailyMetrics.scan(
        FilterExpression="userId = :uid AND #d = :date",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":uid": userId,
            ":date": date
        }
    )
    metrics = response.get("Items", [{}])
    # Defensive: metrics is always a dict
    if isinstance(metrics, list):
        metrics = metrics[0] if metrics and isinstance(metrics[0], dict) else {}
    elif not isinstance(metrics, dict):
        metrics = {}
    metrics = convert_decimals(metrics)
    return {
        'focused_sports': user_fields.get('focused_sports', ['cycling']),
        'interval_type': user_fields.get('interval_type', 'mix'),
        'ftp': user_fields.get('ftp', 250),
        'weight': metrics.get('weight', 70),
        'weekly_hours': user_fields.get('weekly_hours', 10),
        'recovery_metric': user_fields.get('recovery_metric', 5),
        'intensity_weeks': user_fields.get('intensity_weeks', 3),
        'specific_focus': user_fields.get('specific_focus', 'all-rounder'),
        'illness': metrics.get('illness', 0),
        'injury': metrics.get('injury', 0)
    }

def extract_user_id_from_cognito(event):
    """
    Extract userId from Cognito authentication claims only.
    """
    try:
        # Extract from Cognito authorizer claims (sub is the unique user identifier)
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub')
        
        if not user_id:
            return None  # Allow None for autonomous mode
            
        return user_id
    except Exception as e:
        print(f"Failed to extract userId from Cognito authentication: {str(e)}")
        return None  # Allow None for autonomous mode

def lambda_handler(event, context):
    try:
        # Extract userId from Cognito authentication
        userId = extract_user_id_from_cognito(event) if event else None
        
        # Extract date from request body
        body = {}
        if event and event.get('body'):
            try:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            except json.JSONDecodeError:
                pass
        
        date = body.get('date') if body else None
        
        # If running autonomously (no userId/date in event), run for all users for today
        if not userId and not date:
            # Get all userIds from userTable
            scan = userTable.scan(ProjectionExpression="userId")
            user_ids = [item['userId'] for item in scan.get('Items', []) if 'userId' in item]
            # Use current UTC date
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            results = []
            for uid in user_ids:
                print(f"[DEBUG] Running autonomous training algorithm for user {uid} on {today}")
                # Recursively call lambda_handler for each user
                result = lambda_handler({'userId': uid, 'date': today}, context)
                results.append({"userId": uid, "result": result})
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Ran training algorithm for all users', 'results': results}, default=decimal_default)
            }
        if not userId or not date:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing userId or date'})}
        # Remove all upcoming 'training' workouts in the next 5 days
        today = datetime.strptime(date, "%Y-%m-%d")
        for i in range(5):
            d = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            response = workoutsTable.scan(
                FilterExpression="userId = :uid AND #d = :date AND event_type = :etype",
                ExpressionAttributeNames={"#d": "date"},
                ExpressionAttributeValues={
                    ":uid": userId,
                    ":date": d,
                    ":etype": "training"
                }
            )
            items = convert_decimals(response.get("Items", []))
            items = [w if isinstance(w, dict) else {} for w in items]
            for item in items:
                if 'workoutId' in item:
                    workoutsTable.delete_item(Key={"workoutId": item['workoutId']})
        print("[DEBUG] Removed all upcoming training workouts for user", userId)
        user_fields = get_user_profile_fields(userId, date)
        print("[DEBUG] user_fields:", user_fields)
        history = get_last_7_days_history(userId, date)
        print("[DEBUG] history:", history)
        upcoming_schedule = get_upcoming_schedule(userId, date)
        print("[DEBUG] upcoming_schedule before type check:", upcoming_schedule, type(upcoming_schedule))
        if isinstance(upcoming_schedule, (list, dict)):
            if isinstance(upcoming_schedule, list) and upcoming_schedule:
                print("[DEBUG] upcoming_schedule is a list, using first element:", upcoming_schedule[0])
                upcoming_schedule = upcoming_schedule[0]
            else:
                print("[DEBUG] upcoming_schedule is empty or dict, setting to 0")
                upcoming_schedule = 0
        if not isinstance(upcoming_schedule, (int, float)):
            try:
                upcoming_schedule = float(upcoming_schedule)
            except Exception as e:
                print("[DEBUG] Error converting upcoming_schedule to float:", e)
                upcoming_schedule = 0
        print("[DEBUG] upcoming_schedule after type check:", upcoming_schedule, type(upcoming_schedule))
        # Always ensure upcoming_schedule is a list for TrainingAlgorithm compatibility
        if not isinstance(upcoming_schedule, list):
            upcoming_schedule = [upcoming_schedule]
        goals, events, sessions = get_goals_events_sessions(userId, date)
        print("[DEBUG] goals:", goals)
        print("[DEBUG] events:", events)
        print("[DEBUG] sessions:", sessions)
        user_profile = {
            'focused_sports': user_fields['focused_sports'],
            'sports': SPORTS,
            'interval_type': user_fields['interval_type'],
            'upcoming_schedule': upcoming_schedule,
            'ftp': user_fields['ftp'],
            'weight': user_fields['weight'],
            'weekly_hours': user_fields['weekly_hours'],
            'recovery_metric': user_fields['recovery_metric'],
            'intensity_weeks': user_fields['intensity_weeks'],
            'specific_focus': user_fields['specific_focus'],
            'illness': user_fields['illness'],
            'injury': user_fields['injury'],
            'history': history,
            'goals': goals,
            'events': events,
            'sessions': sessions
        }
        print("[DEBUG] user_profile:", user_profile)
        results = []
        max_recursions = min(5, user_profile.get('intensity_weeks', 1))
        current_date = datetime.strptime(date, "%Y-%m-%d")
        for i in range(max_recursions):
            print(f"[DEBUG] Recursion {i}, user_profile['upcoming_schedule']:", user_profile['upcoming_schedule'], type(user_profile['upcoming_schedule']))
            # Always ensure user_profile['upcoming_schedule'] is a list for TrainingAlgorithm
            if not isinstance(user_profile['upcoming_schedule'], list):
                user_profile['upcoming_schedule'] = [user_profile['upcoming_schedule']]
            print(f"[DEBUG] Running TrainingAlgorithm for {current_date.strftime('%Y-%m-%d')}")
            algorithm = TrainingAlgorithm(user_profile, current_date.strftime("%Y-%m-%d"))
            training_day = algorithm.generate_training_day()
            print(f"[DEBUG] training_day for {current_date.strftime('%Y-%m-%d')}:", training_day)
            # training_day is a list of sessions, not a dict
            for session in training_day:
                print("[DEBUG] session:", session, type(session))
                workoutId = str(uuid.uuid4())
                # Ensure all required fields are present
                item = {
                    "workoutId": workoutId,
                    "userId": userId,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "name": session.get("title", "Workout"),
                    "description": session.get("description", ""),
                    "tss": session.get("tss", 0),
                    "tss_type": "estimated",
                    "time": session.get("hours", 0) * 3600,
                    "sport": session.get("type", "cycling"),
                    "completed": session.get("completed", False),
                    "event_type": "Training"
                }
                # Add any other session fields
                for key, value in session.items():
                    if key not in item:
                        item[key] = value
                if 'session_focus' not in item:
                    item['session_focus'] = session.get('session_focus', None)
                print("[DEBUG] Writing item to workoutsTable:", item)
                workoutsTable.put_item(Item=to_dynamodb_decimals(item))
            results.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'training_day': training_day
            })
            # Move to next day and rerun the algorithm for that day
            current_date += timedelta(days=1)
            # Rebuild user_profile for the new date
            user_fields = get_user_profile_fields(userId, current_date.strftime("%Y-%m-%d"))
            history = get_last_7_days_history(userId, current_date.strftime("%Y-%m-%d"))
            upcoming_schedule = get_upcoming_schedule(userId, current_date.strftime("%Y-%m-%d"))
            if isinstance(upcoming_schedule, (list, dict)):
                if isinstance(upcoming_schedule, list) and upcoming_schedule:
                    upcoming_schedule = upcoming_schedule[0]
                else:
                    upcoming_schedule = 0
            if not isinstance(upcoming_schedule, (int, float)):
                try:
                    upcoming_schedule = float(upcoming_schedule)
                except Exception:
                    upcoming_schedule = 0
            if not isinstance(upcoming_schedule, list):
                upcoming_schedule = [upcoming_schedule]
            goals, events, sessions = get_goals_events_sessions(userId, current_date.strftime("%Y-%m-%d"))
            user_profile = {
                'focused_sports': user_fields['focused_sports'],
                'sports': SPORTS,
                'interval_type': user_fields['interval_type'],
                'upcoming_schedule': upcoming_schedule,
                'ftp': user_fields['ftp'],
                'weight': user_fields['weight'],
                'weekly_hours': user_fields['weekly_hours'],
                'recovery_metric': user_fields['recovery_metric'],
                'intensity_weeks': user_fields['intensity_weeks'],
                'specific_focus': user_fields['specific_focus'],
                'illness': user_fields['illness'],
                'injury': user_fields['injury'],
                'history': history,
                'goals': goals,
                'events': events,
                'sessions': sessions
            }
        print("[DEBUG] Finished all recursions")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Training days added to workoutsTable', 'results': results}, default=decimal_default)
        }
    except Exception as e:
        import traceback
        print("[ERROR] Exception in lambda_handler:", str(e))
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
