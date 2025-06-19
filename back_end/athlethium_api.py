from aws_cdk import (
    aws_apigateway as apigateway,
)

from .athlethium_lambdas import athlethiumLambdas



class athlethiumAPI:

    def create_api(self, stack, user_pool, lambdas):
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            stack, "athlethiumAuthorizer", cognito_user_pools=[user_pool]
        )

        api = apigateway.RestApi(
            stack,
            "athlethiumApi",
            rest_api_name="athlethiumApi",
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
            },
        )

        # Create usage plan with rate limiting
        usage_plan = apigateway.UsagePlan(
            stack,
            "athlethiumUsagePlan",
            name="AthlethiumStandardPlan",
            description="Standard usage plan for Athlethium API",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,   # 100 requests per second per user
                burst_limit=200   # 200 requests burst capacity per user
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,      # 10,000 requests per day
                period=apigateway.Period.DAY
            )
        )

        # Add API to usage plan after deployment
        usage_plan.add_api_stage(
            api=api,
            stage=api.deployment_stage
        )

        def add_method(
            root,
            method,
            lambda_handler,
            name="",
            method_responses=None,
            request_parameters=None,
            authorization=True,
        ):
            method_obj = root.add_method(
                method,
                apigateway.LambdaIntegration(lambdas[lambda_handler]),
                authorization_type=(
                    apigateway.AuthorizationType.COGNITO
                    if authorization
                    else apigateway.AuthorizationType.NONE
                ),
                authorizer=authorizer if authorization else None,
                operation_name=name,
                method_responses=method_responses,
                request_parameters=request_parameters,
            )
            
            return method_obj

        # /details - User details endpoints
        details = api.root.add_resource("details")
        
        # /details
        add_method(details, "GET", "get_user_details", "Get User Details")
        
        # /details
        add_method(details, "PUT", "update_user_details", "Update User Details")

        # /signup - User signup endpoint
        signup = api.root.add_resource("signup")
        
        # /signup
        add_method(signup, "PUT", "user_signup", "User Signup")

        # /metrics - User metrics endpoints
        metrics = api.root.add_resource("metrics")
        
        # /metrics
        add_method(metrics, "GET", "get_user_metrics", "Get User Metrics")
        
        # /metrics
        add_method(metrics, "PUT", "update_user_metrics", "Update User Metrics")
        
        # /metrics/range - Simplified date range endpoint
        metrics_range = metrics.add_resource("range")
        add_method(metrics_range, "GET", "get_user_metrics_range", "Get User Metrics Range")

        # /schedule - User schedule endpoints
        schedule = api.root.add_resource("schedule")
        
        # /schedule
        add_method(schedule, "GET", "get_user_schedule", "Get User Schedule")
        
        # /schedule
        add_method(schedule, "PUT", "update_user_schedule", "Update User Schedule")

        # /session - Training session endpoints
        session = api.root.add_resource("session")
        
        # /session
        add_method(session, "POST", "add_training", "Add Training Session")
        
        # /session
        add_method(session, "GET", "get_training_session", "Get Training Session")
        
        # /session
        add_method(session, "PUT", "update_session_details", "Update Training Session")
        
        # /session
        add_method(session, "DELETE", "delete_session_details", "Delete Training Session")

        # /training - Training related endpoints
        training = api.root.add_resource("training")
        
        # /training
        add_method(training, "GET", "get_user_training", "Get User Training")
        
        # /training
        add_method(training, "POST", "training_algorithm", "Run Training Algorithm")

        # /account - Account management endpoints
        account = api.root.add_resource("account")
        
        # /account - Delete account (permanently delete all user data)
        add_method(account, "DELETE", "account_delete", "Delete User Account")
        
        # /account - Export user data
        add_method(account, "GET", "account_export", "Export User Data")

        # /chats - Chat system endpoints
        chats = api.root.add_resource("chats")
        
        # /chats - Get chat messages
        add_method(chats, "GET", "chat_get_messages", "Get Chat Messages")
        
        # /chats - Send chat message
        add_method(chats, "POST", "chat_send_message", "Send Chat Message")
        
        # /chats/history - Get chat history
        history = chats.add_resource("history")
        add_method(history, "GET", "chat_get_history", "Get Chat History")

        return api
