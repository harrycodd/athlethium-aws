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
from .athlethium_buckets import athlethiumBuckets

class athlethiumLambdas:
    def __init__(self):
        self.lambdas = {}

    def __getitem__(self, item):
        return self.lambdas[item]

    def create_lambdas(self, stack, tables:athlethiumDB, cognito:athlethiumCognito, buckets:athlethiumBuckets):
        numpy_layer = NumpyLayer(stack, "NumpyLayer").layer
        anthropic_layer = AnthropicLayer(stack, "AnthropicLayer").layer

        def create_lambda(name, lambda_path_relative, tables_to_access=None, environment_vars=None):
            lambda_path = str(Path(__file__).resolve().parent.parent / "api_lambda" / lambda_path_relative)
            lambda_function = _lambda.Function(
                stack, name,
                runtime=_lambda.Runtime.PYTHON_3_11,
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

        self.update_user_details.add_permission(
            "CognitoTriggerPermission",
            principal=iam.ServicePrincipal("cognito-idp.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=cognito.user_pool.user_pool_arn
        )

        self.user_signup = create_lambda("user_signup", "signup", [tables.userTable, tables.dailyMetrics, tables.workoutsTable, tables.trainingSchedule])

        self.get_user_metrics = create_lambda("get_user_metrics", "metrics/get", [tables.userTable, tables.dailyMetrics, tables.workoutsTable])
        self.update_user_metrics = create_lambda("update_user_metrics", "metrics/update", [tables.userTable, tables.dailyMetrics])
        self.get_user_metrics_range = create_lambda("get_user_metrics_range", "metrics/range", [tables.userTable, tables.dailyMetrics, tables.workoutsTable])

        self.get_user_schedule = create_lambda("get_user_schedule", "schedule/get", [tables.userTable, tables.trainingSchedule])
        self.update_user_schedule = create_lambda("update_user_schedule", "schedule/update", [tables.userTable, tables.trainingSchedule])

        self.get_user_training = create_lambda("get_user_training", "training/get", [tables.userTable, tables.workoutsTable])

        self.get_user_goals = create_lambda("get_user_goals", "training/get", [tables.userTable, tables.workoutsTable])

        self.update_session_details = create_lambda("update_session_details", "session/update", [tables.workoutsTable])
        self.delete_session_details = create_lambda("delete_session_details", "session/delete", [tables.workoutsTable])

        self.get_training_session = create_lambda("get_training_session", "session/get", [tables.workoutsTable])

        self.add_training = create_lambda("add_training", "session/add", [tables.workoutsTable])

        self.training_algorithm = create_lambda("training_algorithm", "training/run", [tables.userTable, tables.dailyMetrics, tables.workoutsTable, tables.trainingSchedule])

        # Scheduled Training Algorithm Lambda
        self.scheduled_training_algorithm = _lambda.Function(
            stack, "scheduled_training_algorithm",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(str(Path(__file__).resolve().parent.parent / "api_lambda" / "training/scheduler")),
            function_name="scheduled_training_algorithm",
            timeout=aws_cdk.Duration.minutes(15),  # Longer timeout for processing all users
            layers=[numpy_layer, anthropic_layer],
        )
        
        # Grant permissions to all relevant tables
        for table in [tables.userTable, tables.workoutsTable, tables.goalsTable, tables.userSessionsTable, tables.dailyMetrics]:
            table.grant_read_write_data(self.scheduled_training_algorithm)
        
        self.lambdas["scheduled_training_algorithm"] = self.scheduled_training_algorithm

        # Account management endpoints (with longer timeout for data processing)
        self.account_delete = _lambda.Function(
            stack, "account_delete",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(str(Path(__file__).resolve().parent.parent / "api_lambda" / "account" / "delete")),
            function_name="account_delete",
            timeout=aws_cdk.Duration.seconds(60),  # Longer timeout for deletion operations
            layers=[numpy_layer, anthropic_layer],
        )
        
        self.account_export = _lambda.Function(
            stack, "account_export",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(str(Path(__file__).resolve().parent.parent / "api_lambda" / "account" / "export")),
            function_name="account_export",
            timeout=aws_cdk.Duration.seconds(60),  # Longer timeout for data export
            layers=[numpy_layer, anthropic_layer],
        )

        # Chat system endpoints (with longer timeout for AI processing)
        self.chat_send_message = _lambda.Function(
            stack, "chat_send_message",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(str(Path(__file__).resolve().parent.parent / "api_lambda" / "chats/send_message")),
            function_name="chat_send_message",
            timeout=aws_cdk.Duration.seconds(30),  # Longer timeout for AI processing
            layers=[numpy_layer, anthropic_layer]
        )
        
        self.chat_get_messages = create_lambda("chat_get_messages", "chats/get", [tables.chatTable])
        self.chat_get_history = create_lambda("chat_get_history", "chats/history/get", [tables.chatTable])

        # Grant database permissions to chat lambdas
        for table in [tables.userTable, tables.dailyMetrics, tables.trainingSchedule, tables.workoutsTable, tables.chatTable]:
            table.grant_read_write_data(self.chat_send_message)
        
        # Grant Secrets Manager permission to chat lambda for Anthropic API key
        secret_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "secretsmanager:GetSecretValue"
            ],
            resources=[
                f"arn:aws:secretsmanager:eu-west-2:*:secret:anthropic-api-key*"
            ]
        )
        self.chat_send_message.add_to_role_policy(secret_policy)
        
        tables.chatTable.grant_read_data(self.chat_get_messages)
        tables.chatTable.grant_read_data(self.chat_get_history)

        # Grant database permissions to account management lambdas
        for table in [tables.userTable, tables.dailyMetrics, tables.trainingSchedule, tables.workoutsTable, tables.partnerTokens]:
            table.grant_read_write_data(self.account_delete)
            table.grant_read_data(self.account_export)

        # Grant S3 permissions to account management lambdas
        buckets.workoutsBucket.grant_read_write(self.account_delete)
        buckets.workoutsBucket.grant_read(self.account_export)
        
        # Grant SES permissions to account export lambda for sending emails
        ses_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ses:SendRawEmail",
                "ses:SendEmail"
            ],
            resources=[
                f"arn:aws:ses:eu-west-2:*:identity/code.athlethium.com",
                f"arn:aws:ses:eu-west-2:*:identity/export@code.athlethium.com",
                f"arn:aws:ses:eu-west-2:*:identity/data.athlethium.com",
                f"arn:aws:ses:eu-west-2:*:identity/export@data.athlethium.com"
            ]
        )
        self.account_export.add_to_role_policy(ses_policy)
        
        # Add to lambdas dictionary
        self.lambdas["account_delete"] = self.account_delete
        self.lambdas["account_export"] = self.account_export
        self.lambdas["chat_send_message"] = self.chat_send_message
        self.lambdas["chat_get_messages"] = self.chat_get_messages
        self.lambdas["chat_get_history"] = self.chat_get_history

        # Schedule for 3am GMT daily
        daily_rule = events.Rule(
            stack, "DailyTrainingAlgorithmSchedule",
            schedule=events.Schedule.cron(minute="0", hour="3")
        )
        daily_rule.add_target(targets.LambdaFunction(self.scheduled_training_algorithm))

        cognito.user_pool.add_trigger(
            UserPoolOperation.POST_CONFIRMATION,
            self.update_user_details
        )
        self.lambdas["auto_confirm_email_lambda"] = self.update_user_details