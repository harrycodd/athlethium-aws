from pathlib import Path
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
)
import aws_cdk
from .cdk_numpy_layer import NumpyLayer
from .cdk_anthropic_layer import AnthropicLayer
from aws_cdk.aws_cognito import UserPoolOperation

from .athlethium_cognito import athlethiumCognito
from .athlethium_databases import athlethiumDB

class athlethiumLambdas:
    def __init__(self):
        self.lambdas = {}

    def __getitem__(self, item):
        return self.lambdas[item]

    def create_lambdas(self, stack, tables:athlethiumDB, cognito:athlethiumCognito):
        numpy_layer = NumpyLayer(stack, "NumpyLayer").layer
        anthropic_layer = AnthropicLayer(stack, "AnthropicLayer").layer

        def create_lambda(name, lambda_path_relative, tables_to_access=None, environment_vars=None):
            lambda_path = str(Path(__file__).resolve().parent.parent / "api_lambda" / lambda_path_relative)
            lambda_function = _lambda.Function(
                stack, name,
                runtime=_lambda.Runtime.PYTHON_3_11,  # Updated to match layer
                handler="lambda_function.lambda_handler",
                code=_lambda.Code.from_asset(lambda_path),
                function_name=name,
                timeout=aws_cdk.Duration.seconds(10),
                layers=[numpy_layer, anthropic_layer],
                environment=environment_vars or {}
            )

            if tables_to_access:
                for table in tables_to_access:
                    table.grant_read_write_data(lambda_function)

            self.lambdas[name] = lambda_function
            return lambda_function

        self.get_user_details = create_lambda("get_user_details", "details/get", [tables.userTable])
        self.update_user_details = create_lambda('update_user_details', "details/update", [tables.userTable])
        self.delete_user_details = create_lambda("delete_user_details", "details/delete", [tables.userTable])

        self.update_user_details.add_permission(
            "CognitoTriggerPermission",
            principal=iam.ServicePrincipal("cognito-idp.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=cognito.user_pool.user_pool_arn
        )

        self.delete_user_details.add_permission(
            "CognitoTriggerPermission",
            principal=iam.ServicePrincipal("cognito-idp.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=cognito.user_pool.user_pool_arn
        )

        self.get_user_metrics = create_lambda("get_user_metrics", "metrics/get", [tables.userTable, tables.dailyMetrics, tables.workoutsTable])
        self.update_user_metrics = create_lambda("update_user_metrics", "metrics/update", [tables.userTable, tables.dailyMetrics])

        self.get_user_schedule = create_lambda("get_user_schedule", "schedule/get", [tables.userTable, tables.trainingSchedule])
        self.update_user_schedule = create_lambda("update_user_schedule", "schedule/update", [tables.userTable, tables.trainingSchedule])

        self.get_user_training = create_lambda("get_user_training", "training/get", [tables.userTable, tables.workoutsTable])

        self.get_user_goals = create_lambda("get_user_goals", "training/get", [tables.userTable, tables.workoutsTable])

        self.update_session_details = create_lambda("update_session_details", "session/update", [tables.workoutsTable])
        self.delete_session_details = create_lambda("delete_session_details", "session/delete", [tables.workoutsTable])    

        self.get_training_session = create_lambda("get_training_session", "session/get", [tables.workoutsTable])

        self.add_training = create_lambda("add_training", "session/add", [tables.workoutsTable])

        # Strava webhook Lambda functions - TODO: Create actual lambda functions in partner/strava/webhooks/
        # self.strava_webhook_verify = create_lambda(
        #     "strava_webhook_verify",
        #     "partner/strava/webhooks/verify",
        #     environment_vars={
        #         'STRAVA_VERIFY_TOKEN': 'athlethium_strava_webhook_2024'  # Change this to your desired verify token
        #     }
        # )
        # self.strava_webhook_handler = create_lambda(
        #     "strava_webhook_handler", 
        #     "partner/strava/webhooks/handler",
        #     [tables.userTable, tables.workoutsTable]
        # )

        # Wahoo webhook Lambda functions - TODO: Create actual lambda functions in partner/wahoo/webhooks/
        # self.wahoo_webhook_verify = create_lambda(
        #     "wahoo_webhook_verify",
        #     "partner/wahoo/webhooks/verify",
        #     environment_vars={
        #         'WAHOO_VERIFY_TOKEN': 'athlethium_wahoo_webhook_2024'  # Change this to your desired verify token
        #     }
        # )
        # self.wahoo_webhook_handler = create_lambda(
        #     "wahoo_webhook_handler", 
        #     "partner/wahoo/webhooks/handler",
        #     [tables.userTable, tables.workoutsTable]
        # )

        # Strava OAuth Lambda functions - TODO: Create actual lambda functions in partner/strava/auth/
        # self.strava_oauth_initiate = create_lambda(
        #     "strava_oauth_initiate",
        #     "partner/strava/auth/initiate",
        #     environment_vars={
        #         'STRAVA_CLIENT_ID': '157155',  # Set this to your Strava app's client ID
        #         'STRAVA_REDIRECT_URI': 'https://api.athlethium.com/auth/strava/callback'  # Update with your actual domain
        #     }
        # )
        # self.strava_oauth_callback = create_lambda(
        #     "strava_oauth_callback",
        #     "partner/strava/auth/callback",
        #     [tables.userTable],
        #     environment_vars={
        #         'STRAVA_CLIENT_ID': '157155',
        #         'STRAVA_CLIENT_SECRET': '39c931d545bc2360fe9f40f265ae9780420bf79d'  # Set this to your Strava app's client secret
        #     }
        # )
        # self.strava_token_refresh = create_lambda(
        #     "strava_token_refresh",
        #     "partner/strava/auth/refresh",
        #     [tables.userTable],
        #     environment_vars={
        #         'STRAVA_CLIENT_ID': '157155',
        #         'STRAVA_CLIENT_SECRET': '39c931d545bc2360fe9f40f265ae9780420bf79d'
        #     }
        # )
        # self.strava_deauthorize = create_lambda(
        #     "strava_deauthorize",
        #     "partner/strava/auth/deauthorize",
        #     [tables.userTable]
        # )

        # Chat Lambda functions - TODO: Create actual lambda functions in chats/
        # self.get_chats = create_lambda("get_chats", "chats/get", [tables.userTable])
        # self.get_chat_history = create_lambda("get_chat_history", "chats/history", [tables.userTable])
        # self.send_chat_message = create_lambda("send_chat_message", "chats/send_message", [tables.userTable])

        # Register the training_algorithm Lambda and grant table access
        self.training_algorithm = create_lambda("training_algorithm", "training/run", [tables.userTable, tables.dailyMetrics, tables.workoutsTable, tables.trainingSchedule])

        # Schedule the training_algorithm Lambda to run daily at 2am UTC
        daily_rule = events.Rule(
            stack, "DailyTrainingAlgorithmSchedule",
            schedule=events.Schedule.cron(minute="0", hour="2")
        )
        daily_rule.add_target(targets.LambdaFunction(self.training_algorithm))

        # Register the update_user_details Lambda for Cognito Post Confirmation trigger (merged logic)
        cognito.user_pool.add_trigger(
            UserPoolOperation.POST_CONFIRMATION,
            self.update_user_details
        )
        self.lambdas["auto_confirm_email_lambda"] = self.update_user_details