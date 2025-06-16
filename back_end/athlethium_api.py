from aws_cdk import (
    aws_apigateway as apigateway,
)

from .athlethium_lambdas import athlethiumLambdas



class athlethiumAPI:

    def create_api(self, stack, user_pool, lambdas):
        def add_method(
            root,
            method,
            lambda_handler,
            name="",
            method_responses=None,
            request_parameters=None,
            authorization=True,
        ):
            root.add_method(
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

        # /details - User details endpoints
        details = api.root.add_resource("details")
        
        # /details/get
        details_get = details.add_resource("get")
        add_method(details_get, "GET", "get_user_details", "Get User Details")
        
        # /details/update
        details_update = details.add_resource("update")
        add_method(details_update, "PUT", "update_user_details", "Update User Details")
        
        # /details/delete
        details_delete = details.add_resource("delete")
        add_method(details_delete, "DELETE", "delete_user_details", "Delete User Details")

        # /metrics - User metrics endpoints
        metrics = api.root.add_resource("metrics")
        
        # /metrics/get
        metrics_get = metrics.add_resource("get")
        add_method(metrics_get, "GET", "get_user_metrics", "Get User Metrics")
        
        # /metrics/update
        metrics_update = metrics.add_resource("update")
        add_method(metrics_update, "PUT", "update_user_metrics", "Update User Metrics")

        # /schedule - User schedule endpoints
        schedule = api.root.add_resource("schedule")
        
        # /schedule/get
        schedule_get = schedule.add_resource("get")
        add_method(schedule_get, "GET", "get_user_schedule", "Get User Schedule")
        
        # /schedule/update
        schedule_update = schedule.add_resource("update")
        add_method(schedule_update, "PUT", "update_user_schedule", "Update User Schedule")

        # /session - Training session endpoints
        session = api.root.add_resource("session")
        
        # /session/add
        session_add = session.add_resource("add")
        add_method(session_add, "POST", "add_training", "Add Training Session")
        
        # /session/get
        session_get = session.add_resource("get")
        add_method(session_get, "GET", "get_training_session", "Get Training Session")
        
        # /session/update
        session_update = session.add_resource("update")
        add_method(session_update, "PUT", "update_session_details", "Update Training Session")
        
        # /session/delete
        session_delete = session.add_resource("delete")
        add_method(session_delete, "DELETE", "delete_session_details", "Delete Training Session")

        # /training - Training related endpoints
        training = api.root.add_resource("training")
        
        # /training/get
        training_get = training.add_resource("get")
        add_method(training_get, "GET", "get_user_training", "Get User Training")
        
        # /training/run
        training_run = training.add_resource("run")
        add_method(training_run, "POST", "training_algorithm", "Run Training Algorithm")

        # /partner - Partner integrations (Commented out until lambda functions are implemented)
        # partner = api.root.add_resource("partner")
        
        # # /partner/strava
        # strava = partner.add_resource("strava")
        
        # # /partner/strava/webhooks
        # strava_webhooks = strava.add_resource("webhooks")
        # add_method(strava_webhooks, "POST", "strava_webhook_verify", "Strava Webhook Verification", authorization=False)
        # add_method(strava_webhooks, "POST", "strava_webhook_handler", "Strava Webhook Handler", authorization=False)
        
        # # /partner/strava/auth
        # strava_auth = strava.add_resource("auth")
        # strava_authorize = strava_auth.add_resource("authorize")
        # add_method(strava_authorize, "POST", "strava_oauth_initiate", "Initiate Strava OAuth", authorization=True)
        
        # strava_callback = strava_auth.add_resource("callback")
        # add_method(strava_callback, "POST", "strava_oauth_callback", "Strava OAuth Callback", authorization=False)
        
        # strava_refresh = strava_auth.add_resource("refresh")
        # add_method(strava_refresh, "POST", "strava_token_refresh", "Refresh Strava Token", authorization=True)
        
        # strava_deauth = strava_auth.add_resource("deauthorize")
        # add_method(strava_deauth, "POST", "strava_deauthorize", "Deauthorize Strava", authorization=True)
        
        # # /partner/wahoo
        # wahoo = partner.add_resource("wahoo")
        
        # # /partner/wahoo/webhooks
        # wahoo_webhooks = wahoo.add_resource("webhooks")
        # add_method(wahoo_webhooks, "POST", "wahoo_webhook_verify", "Wahoo Webhook Verification", authorization=False)
        # add_method(wahoo_webhooks, "POST", "wahoo_webhook_handler", "Wahoo Webhook Handler", authorization=False)
        
        # # /partner/wahoo/auth (placeholder for future wahoo auth endpoints)
        # wahoo_auth = wahoo.add_resource("auth")

        # /chats - Chat related endpoints (Commented out until lambda functions are implemented)
        # chats = api.root.add_resource("chats")
        # add_method(chats, "GET", "get_chats", "Get Chats")
        # chats_history = chats.add_resource("history")
        # add_method(chats_history, "GET", "get_chat_history", "Get Chat History")
        # chats_send = chats.add_resource("send")
        # add_method(chats_send, "POST", "send_chat_message", "Send Chat Message")

        return api
