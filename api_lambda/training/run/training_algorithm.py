import datetime
import uuid
import json
import os
import random
import boto3

"""
TO DO
ADD DATABASE TO GOAL, SESSION, STRENGTH, YOGA
IMPLEMENT RACE SIM LOGIC AT SOME POINT 
"""

dynamodb = boto3.resource('dynamodb', region_name="eu-west-2")
workoutsTable = dynamodb.Table("workoutsTable")
goalsTable = dynamodb.Table("goalsTable")

def add_goal(goal):
    """Add a goal to the goals table"""
    try:
        goalId = str(uuid.uuid4())
        goal_item = {
            "goalId": goalId,
            "userId": goal.get("userId", ""),
            "name": goal["name"],
            "date": goal["date"].strftime('%Y-%m-%d') if isinstance(goal["date"], datetime.date) else goal["date"],
            "type": goal["type"],
            "sports": goal["sports"]
        }
        
        goalsTable.put_item(Item=goal_item)
        print(f"Successfully added goal {goalId} to DynamoDB")
        return goalId
    except Exception as e:
        print(f"Error adding goal to DynamoDB: {str(e)}")
        return None

def load_workout_library():
    """Load workout library from the workout.json file."""
    file_locations = [
        os.path.join(os.path.dirname(__file__), 'workout.json'),
        'workout.json',
        './workout.json'
    ]
    
    workouts = None
    for file_path in file_locations:
        try:
            with open(file_path, 'r') as file:
                print(f"Loading workout library from {file_path}")
                workouts = json.load(file)
                break
        except (FileNotFoundError, IOError) as e:
            continue
            
    if workouts is None:
        raise FileNotFoundError("Could not find workout.json file")
    
    return workouts

def get_session(intensity, length, sport, userId, date, user_profile):
    workoutId = str(uuid.uuid4())
    
    # Load workout library
    workout_library = load_workout_library()
    
    # Get workouts for the specified sport and intensity
    if sport in workout_library and str(intensity) in workout_library[sport]:
        available_workouts = workout_library[sport][str(intensity)]
        
        # Filter workouts based on duration
        suitable_workouts = [
            w for w in available_workouts 
            if w["min_duration"] <= length <= w["max_duration"]
        ]
        
        # Select a workout (random or first if filtered)
        session = random.choice(suitable_workouts) if suitable_workouts else available_workouts[0]
        
        # Calculate TSS multiplier
        tss_multiplier = session.get("tss_multiplier", 0)
        if intensity == -1:
            tss_multiplier = 0
        elif intensity == 0:
            tss_multiplier = 20
        elif intensity == 1:
            tss_multiplier = 40
        elif intensity == 2:
            tss_multiplier = 60
        elif intensity == 3:
            tss_multiplier = 80
        elif intensity == 4:
            tss_multiplier = 60
        elif intensity == 5:
            tss_multiplier = 60
        elif intensity == 6:
            tss_multiplier = 70
        
        if "strength" in sport or "yoga" in sport:
            tss_multiplier = 0
            description = session.get("structured", "")
        
        # Create description from structured or non-structured content
        elif user_profile["interval_type"] == "mix":
            description = f"A choice of: \n{session.get("structured", "")} \nor \n{session.get("non-structured", "")}.\nThe structured workout has been loaded on you computer for your convinience."
        else:
            description = session.get(user_profile["interval_type"], "")
        
        item = {
            "workoutId": workoutId,
            "userId": userId,
            "date": date,
            "name": session.get("name", "Workout"),
            "description": description,
            "tss": length * tss_multiplier,
            "tss_type": "estimated",
            "time": length * 3600,
            "sport": sport,
            "completed": False,
            "event_type": "Training"
        }
        
    else:
        print(f"No workouts found for sport={sport}, intensity={intensity}")
        item = {
            "workoutId": workoutId,
            "userId": userId,
            "date": date,
            "name": f"{sport.capitalize()} Workout",
            "description": "Generic workout",
            "tss": length * 40,
            "tss_type": "estimated",
            "time": length * 3600,
            "sport": sport,
            "completed": False,
            "event_type": "Training"
        }
        
    try:
        workoutsTable.put_item(Item=item)
        print(f"Successfully stored generic workout {workoutId} in DynamoDB")
    except Exception as e:
        print(f"Error storing workout in DynamoDB: {str(e)}")


def recovery_day(user_profile, userId, date):
    if user_profile["upcoming_schedule"] >= 1:
        return get_session(0, 1, user_profile["focused_sports"][0], userId, date, user_profile)
    return get_session(-1, 0, "", userId, date, user_profile)   

def training_algorithm(user_profile, date, userId):
    tomorrow = date + datetime.timedelta(days=1)
    day_after = date + datetime.timedelta(days=2)

    # Define endurance sports early
    endurance_sport = [sport for sport in user_profile["sports"] if sport in ['cycling', 'running', 'swimming']]

    #Serverly ill logic
    if user_profile["injury"] == 2 or user_profile["illness"] == 2:
        return get_session(-1, 0, "", userId, date, user_profile)
    
    #Goal logic
    if not user_profile["goal"] or len(user_profile["goal"]) == 0:
        goal_date = date + datetime.timedelta(weeks=12)
        days_until = (goal_date - date).days
        goal_name = "Artifical Goal"
        goal_type = "artificalGoal"
        goal = {
            "userId": userId,
            "name": goal_name,
            "date": goal_date,
            "type": goal_type,
            "sports": user_profile["focused_sports"]
        }
        add_goal(goal)

    else:
        goal = user_profile["goal"]
        goal_date = datetime.strptime(goal["date"], "%Y-%m-%d").date()
        days_until = (goal_date - date).days
        if days_until > 365:
            goal_date = date + datetime.timedelta(weeks=12)
            goal_name = "Artifical Goal"
            goal_type = "artificalGoal"
            goal = {
                "name": goal_name,
                "date": goal_date,
                "type": goal_type,
                "sports": goal["sports"]
            }
            add_goal(goal)
        else:
            while days_until > 12*7:
                goal_date = goal_date - datetime.timedelta(weeks=12)
                goal_name = "Artifical Goal"
                goal_type = "artificalGoal"
                days_until = (goal_date - date).days
                goal = {
                    "userId": userId,
                    "name": goal_name,
                    "date": goal_date,
                    "type": goal_type,
                    "sports": goal["sports"]
                }
                add_goal(goal)

    hard_weeks_divisor = user_profile["intensity_weeks"] + 1
    weeks_till_goal = (goal_date - date).days // 7
    relative_week = (weeks_till_goal % hard_weeks_divisor)
    hard_week = relative_week != 0 
    if user_profile["illness"] == 1 or user_profile["injury"] == 1:
        hard_week = False

    #Taper logic for goals
    if days_until < 3:
        if days_until == 0:
            return
        elif days_until == 1:
            sport_to_do = goal["sports"][0]
            for i in goal["sports"]:
                if i < sport_to_do:
                    sport_to_do = i
            return get_session(7, min(2, user_profile["weekly_hours"]/8), sport_to_do, userId, date, user_profile)
        else:
            if user_profile["schedule"][0] >= 1:
                return recovery_day(user_profile, userId, date)
            return get_session(-1, 0, "", userId, date, user_profile)  
        
    #Taper logic for events
    event = user_profile["event"]
    event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
    days_until = (event_date - date).days
    if days_until < 3:
        if days_until == 0:
            return
        elif days_until == 1:
            sport_to_do = goal["sports"][0]
            for i in goal["sports"]:
                if i < sport_to_do:
                    sport_to_do = i
            return get_session(7, min(2, user_profile["weekly_hours"]/8), sport_to_do, userId, date, user_profile)
        else:
            if user_profile["schedule"][0] >= 1:
                return recovery_day(user_profile, userId, date)
            return get_session(-1, 0, "", userId, date, user_profile)  
        
    #Rest day logic
    last_rest_day = 8
    last_recovery_day = 8
    completed_rest_days = 0
    last_cycling_session = 8
    last_running_session = 8
    last_swimming_session = 8
    last_intense_day = 8
    no_completed_session = 0

    endurance_side_sport = [sport for sport in endurance_sport if sport not in user_profile["focused_sports"]]
    sport_session = {}
    for sport in endurance_side_sport:
        sport_session[sport] = 1

    # Calculate no_session first (moved from later in the code)
    if len(endurance_sport) > 1:
        if user_profile["weekly_hours"] <= 6:
            double_days = 0
        elif user_profile["weekly_hours"] <= 10:  # Fixed duplicate condition
            double_days = 1
        elif user_profile["weekly_hours"] <= 14:  # Fixed duplicate condition
            double_days = 2
        else:
            double_days = 3
    else:
        double_days = 0

    recovery_index = user_profile["recovery_metric"]
    if recovery_index == 1:
        rest_days = 4
    elif recovery_index == 2:
        rest_days = 3
    elif recovery_index == 3:
        rest_days = 2
    elif recovery_index == 4:
        rest_days = 1
    else: 
        rest_days = 1

    no_session = 7 + double_days - rest_days  # Fixed from 8 to 7 (days in week)

    sessions_left = no_session - sum(sport_session.values())  # Fixed method call
    session_no_focused_sport = round(sessions_left / len(user_profile["focused_sports"]))

    for sport in user_profile["focused_sports"]:
        sport_session[sport] = session_no_focused_sport

    sport_session_schedule = sport_session.copy()
    total_focus = {
        -1: 0,
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0
    }

    for i in range(0, 7):
        if \
        user_profile["history"]["cycling"]["focus"][i] in [-1, 0] and \
        user_profile["history"]["swimming"]["focus"][i] in [-1, 0] and \
        user_profile["history"]["running"]["focus"][i]in [-1, 0]:
            last_rest_day = i
            completed_rest_days += 1

        if \
        user_profile["history"]["cycling"]["focus"][i] > 1 or \
        user_profile["history"]["swimming"]["focus"][i] > 1 or \
        user_profile["history"]["running"]["focus"][i] > 1:
            last_intense_day = i

        if \
        user_profile["history"]["cycling"]["focus"][i] in [0] or \
        user_profile["history"]["swimming"]["focus"][i] in [0] or \
        user_profile["history"]["running"]["focus"][i]in [0]:
            last_recovery_day = i 
            completed_rest_days -= 1

        if user_profile["history"]["cycling"]["focus"][i] not in [-1, 0]:
            no_completed_session += 1
            last_cycling_session = i
            try:
                sport_session_schedule["cycling"] -= 1
            except:
                pass

        if user_profile["history"]["swimming"]["focus"][i] not in [-1, 0]:
            no_completed_session += 1
            last_swimming_session = i
            try:
                sport_session_schedule["swimming"] -= 1
            except:
                pass

        if user_profile["history"]["running"]["focus"][i] not in [-1, 0]:
            no_completed_session += 1
            last_running_session = i
            try:
                sport_session_schedule["running"] -= 1
            except:
                pass

        total_focus[user_profile["history"]["cycling"]["focus"][i]] += 1
        total_focus[user_profile["history"]["running"]["focus"][i]] += 1
        total_focus[user_profile["history"]["swimming"]["focus"][i]] += 1

    # Update rest_day logic based on recovery index
    if recovery_index == 1:
        last_rest_day += 2 
    elif recovery_index == 2:
        last_rest_day += 3
    elif recovery_index == 3:
        last_rest_day += 3
    elif recovery_index == 4:
        last_rest_day += 4 
    else: 
        last_rest_day += 5  

    if last_rest_day >= 7 and user_profile["upcoming_schedule"][0] >= 1:
        if user_profile["upcoming_schedule"][1] >= 1:
            if user_profile["upcoming_schedule"][2] >= 1:
                if last_recovery_day == 8:
                    return get_session(-1, 0, "", userId, date, user_profile)  
            return recovery_day(user_profile, userId, date)

    today_session = []
    tomorrow_session = []
    day_after_session = []
    for session in user_profile["sessions"]:
        session_date = datetime.datetime.strptime(session["date"], "%Y-%m-%d").date()
        if session_date == date:
            today_session.append(session)
        elif session_date == tomorrow:
            tomorrow_session.append(session)
        elif session_date == day_after:
            day_after_session.append(session)

    total_hours = 0

    if \
    double_days > 0 and no_session - no_completed_session > 0 and completed_rest_days <= rest_days and \
    len(tomorrow_session) <= 1 and (len(tomorrow_session) == 0 or not (tomorrow_session[0]["time"] >= 7200 or \
    (user_profile["upcoming_schedule"][1] * 3600) - tomorrow_session[0]["time"] >= 9000)) and \
    today_session == [] and user_profile["upcoming_schedule"][0] >= 3 and hard_week:
        #Double day logic
        if today_session != []:
            total_hours = round(today_session[0]["time"] / 3600)
        if len(endurance_sport) > 2:
            potential_sports = []
            for i in endurance_sport:
                if sport_session_schedule[i] >= 1:
                    potential_sports.append(i)
            
            if len(potential_sports) == 2:
                sports = potential_sports
            else:
                if len(potential_sports) == 0:
                    potential_sports = endurance_sport

                most_recent_days = 0
                sport = potential_sports[0]
                
                for i in potential_sports:
                    if i == "running":
                        if last_running_session > most_recent_days:
                            sport = i
                    elif i == "cycling":
                        if last_cycling_session > most_recent_days:
                            sport = i
                    else:
                        if last_swimming_session > most_recent_days:
                            sport = i
                sports = [sport for sport in potential_sports if sport != sport]
        else:
            sports = endurance_sport

        intensity = {}
        for sport in sports:
            if sport not in user_profile["focused_sports"]:
                intensity[sport] = 1
            elif (total_focus[3] >= 2 and relative_week == 2) or \
            (total_focus[2] >= 1 and total_focus[3] >= 1 and relative_week in [1, 3]):
                intensity[sport] = 1
            else:
                if last_intense_day < 6 and \
                (len([session for session in tomorrow_session if session["intensity"] > 1]) == 0) and \
                (user_profile["upcoming_schedule"][0] <= 2 or \
                (user_profile["upcoming_schedule"][1] > 2)):
                    if relative_week in [1, 3]:
                        intensity[sport] = 3
                        total_focus[3] += 1
                    else:
                        if total_focus[2] == 0:
                            intensity[sport] = 2
                            total_focus[2] += 1
                        else:
                            intensity[sport] = 3
                            total_focus[3] += 1
                else:
                    if last_intense_day < 6:
                        if relative_week in [1, 3] and total_focus[4] == 0:
                            intensity[sport] = 4
                            total_focus[4] += 1
                        elif total_focus[5] == 0:
                            intensity[sport] = 5
                            total_focus[5] += 1
                        else:
                            intensity[sport] = 1
                    else:
                        intensity[sport] = 1

        # Calculate hours
        max_hours = min(((user_profile["ctl"] + 30) * (7 /50)), user_profile["weekly_hours"]) - 0.5
        hours = {}

        total_sport_hours_multiplier = {
            "cycling": 4,
            "running": 2,
            "swimming": 1
        }

        total = 0
        for i in endurance_sport:
            total += total_sport_hours_multiplier[i] 

        for i in endurance_sport:
            total_sport_hours_multiplier[i] /= total

        for sport in sports:
            if intensity[sport] == 1:
                hours[sport] = round((1.5 * max_hours * total_sport_hours_multiplier[sport])  / no_session) / 2
            else:
                hours[sport] = round((max_hours * total_sport_hours_multiplier[sport]) / no_session) / 2
            hours[sport] = min(hours[sport], round(user_profile["upcoming_schedule"][0] - 1) / 2)
            get_session(intensity[sport], hours[sport], sport, userId, date, user_profile)

        total_hours += sum(hours.values()) + 0.5

    elif today_session != [] and len(today_session) > 1:
        for i in today_session:
            total_hours += round(i["time"] / 3600) + 0.5
    else: 
        if today_session != [] and \
        user_profile["upcoming_schedule"][0] * 3600 < 2.5 + today_session[0]["time"]:
            total_hours = round(today_session[0]["time"] / 3600)
        elif today_session != [] and \
        ((today_session[0]["time"] > 3600 or user_profile["weekly_hours"] < 10) and \
        (today_session[0]["time"] > 7200 or user_profile["weekly_hours"] < 14)):
            total_hours = round(today_session[0]["time"] / 3600) + 0.5
        else:
            if today_session != []:
                total_hours = round(today_session[0]["time"] / 3600)
            if len(endurance_sport) > 1:
                potential_sports = []
                for i in endurance_sport:
                    if sport_session_schedule[i] >= 1:
                        potential_sports.append(i)
                
                if len(potential_sports) == 1:
                    sport = potential_sports[0]
                else:
                    if len(potential_sports) == 0:
                        potential_sports = endurance_sport

                    least_recent_days = 10
                    sport = potential_sports[0]
                    
                    for i in potential_sports:
                        if i == "running":
                            if last_running_session < least_recent_days:
                                sport = i
                        elif i == "cycling":
                            if last_cycling_session < least_recent_days:
                                sport = i
                        else:
                            if last_swimming_session < least_recent_days:
                                sport = i
            else:
                sport = endurance_sport[0]

            if hard_week:
                # Race sim needs to be implemented
                
                # Calculate intense days
                # Relative week == 1 or 3 add threshold session 
                # otherwise double vo2 max
                if sport not in user_profile["focused_sports"]:
                    intensity = 1
                elif (total_focus[3] >= 2 and relative_week == 2) or \
                (total_focus[2] >= 1 and total_focus[3] >= 1 and relative_week in [1, 3]):
                    intensity = 1
                else:
                    if last_intense_day < 6 and \
                    (len([session for session in tomorrow_session if session["intensity"] > 1]) == 0) and \
                    (user_profile["upcoming_schedule"][0] <= 2 or \
                    (user_profile["upcoming_schedule"][1] > 2)):
                        if relative_week in [1, 3]:
                            intensity = 3
                        else:
                            if total_focus[2] == 0:
                                intensity = 2
                            else:

                                intensity = 3
                    else:
                        if last_intense_day < 6:
                            if relative_week in [1, 3] and total_focus[4] == 0:
                                intensity = 4
                            elif total_focus[5] == 0:
                                intensity = 5
                            else:
                                intensity = 1
                        else:
                            intensity = 1

            else:
                if total_focus[2] == 0:
                    intensity = 2
                else:
                    intensity = 1

            # Calculate hours
            max_hours = min(((user_profile["ctl"] + 30) * (7 /50)), user_profile["weekly_hours"])

            total_sport_hours_multiplier = {
                "cycling": 4,
                "running": 2,
                "swimming": 1
            }

            total = 0
            for i in endurance_sport:
                total += total_sport_hours_multiplier[i] 

            for i in endurance_sport:
                total_sport_hours_multiplier[i] /= total

            if intensity == 1:
                hours = round((3 * max_hours * total_sport_hours_multiplier[sport])  / no_session) / 2
            else:
                hours = round((2 * max_hours * total_sport_hours_multiplier[sport]) / no_session) / 2
            if total_hours > 0:
                hours = min(hours, user_profile["upcoming_schedule"][0] - total_hours)
            else:
                hours = min(hours, user_profile["upcoming_schedule"][0])

            # Regulate TSS
            if intensity == 1:
                tss_multiplier = 40
            elif intensity == 2:
                tss_multiplier = 60
            elif intensity == 3:
                tss_multiplier = 80
            elif intensity == 4:
                tss_multiplier = 60
            elif intensity == 5:
                tss_multiplier = 60
            elif intensity == 6:
                tss_multiplier = 70

            while (user_profile["atl"] * (6/7)) + ((tss_multiplier * hours)/7) > (user_profile["ctl"] + 30):
                if hours <= 1 and intensity == 1:
                    get_session(0, hours, sport, userId, date, user_profile)
                    break
                if hours <= 2 and intensity > 1:
                    tss_multiplier = 40
                    intensity = 1
                else:
                    hours -= 0.5
            else:
                get_session(intensity, hours, sport, userId, date, user_profile)

            total_hours += hours + 0.5

    # Check for strength and Yoga
    if user_profile["upcoming_schedule"][0] - total_hours >= 0.5:
        if "strength" in user_profile["sports"] and \
        user_profile["history"]["strength"]["hours"][5] == 0 and \
        user_profile["history"]["strength"]["hours"][6] == 0:
            # Set appropriate session duration based on available time
            strength_duration = min(1.0, user_profile["upcoming_schedule"][0] - total_hours)
            
            if (user_profile["upcoming_schedule"][0] - total_hours) < 1:
                # Either upper or lower body based on alternating pattern
                if user_profile.get("last_strength_focus") == "upper":
                    focus = "lower"
                else:
                    focus = "upper"
                    
                # Store this focus for next time (Note: This would need to be saved to DB in real implementation)
                user_profile["last_strength_focus"] = focus
                
                # Get appropriate strength workout
                return get_session(1, strength_duration, f"strength_{focus}", userId, date, user_profile)
            else:
                # Full body workout when more time is available
                return get_session(1, strength_duration, "strength_full", userId, date, user_profile)

        elif "yoga" in user_profile["sports"]:
            # Yoga session with appropriate duration
            yoga_duration = min(1.0, user_profile["upcoming_schedule"][0] - total_hours)
                
            # Get yoga workout
            return get_session(1, yoga_duration, "yoga", userId, date, user_profile)


