from aws_cdk import (
    aws_cognito as cognito,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_route53 as route53,
    aws_route53_targets as targets,
    Duration,
    RemovalPolicy,
    Stack
)
from constructs import Construct


class athlethiumCognito:

    def __init__(self):
        self.identity_pool = None
        self.app_client = None
        self.user_pool = None

    def create_cognito(self, stack):
        self.user_pool = cognito.UserPool(
            stack, "athlethiumUserPool", user_pool_name="athlethiumUserPool",
            self_sign_up_enabled=True,
            #sign_in_case_sensitive=False,  # Make usernames case insensitive
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=False)
            ),
            sign_in_policy=cognito.SignInPolicy(
                allowed_first_auth_factors=cognito.AllowedFirstAuthFactors(
                    password=True,
                    email_otp=True,
                )
            ),
            email=cognito.UserPoolEmail.with_ses(
                ses_region="eu-west-2",
                ses_verified_domain="code.athlethium.com",
                from_email="verification@code.athlethium.com",
                from_name="Athlethium Verification Code"
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            user_verification=cognito.UserVerificationConfig(
                email_subject="Welcome to Athlethium! Verify Your Account",
                email_body=str("""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Athlethium!</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: auto;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
        }
        .code {
            font-size: 20px;
            font-weight: bold;
            color: #007BFF;
            background-color: #e7f1ff;
            padding: 8px;
            border-radius: 5px;
            display: inline-block;
            margin: 15px 0;
        }
        .footer {
            margin-top: 15px;
            font-size: 12px;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Athlethium!</h1>
        <p>Your verification code is:</p>
        <div class="code">{####}</div>
        <p>Code expires in 15 minutes. If you didn't request this, ignore this email.</p>
        <div class="footer">Athlethium</div>
    </div>
</body>"""),                
                email_style=cognito.VerificationEmailStyle.CODE
            ),
            user_invitation=cognito.UserInvitationConfig(
                email_subject="You're Invited to Join Athlethium!",
                email_body="Welcome to Athlethium!\n\nYou've been invited to join our fitness community.\n\nYour login credentials:\nUsername: {username}\nTemporary Password: {####}\n\nGetting started:\n1. Download the Athlethium app\n2. Sign in with your credentials above\n3. Create a new secure password\n4. Start your fitness journey!\n\nSecurity note: Please change your password after your first login. This temporary password expires in 7 days.\n\nWelcome aboard!\nThe Athlethium Team"
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        self.app_client = self.user_pool.add_client(
            "athlethiumAppClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user=True
            )
        )

        self.app_client2 = self.user_pool.add_client(
            "athlethiumAppClient2",
            generate_secret=True,
            auth_flows=cognito.AuthFlow(
                user=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=["https://app.apidog.com/oauth2-browser-callback.html"]           
            )
        )

        self.identity_pool = cognito.CfnIdentityPool(
            stack, "athlethiumIdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[{
                "clientId": self.app_client.user_pool_client_id,
                "providerName": self.user_pool.user_pool_provider_name,
            }],
            identity_pool_name="athlethiumIdentityPool"
        )

        auth_role = iam.Role(
            stack, "CognitoAuthRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {"cognito-identity.amazonaws.com:aud": self.identity_pool.ref},
                    "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "authenticated"}
                },
                "sts:AssumeRoleWithWebIdentity"
            )
        )

        cognito.CfnIdentityPoolRoleAttachment(
            stack, "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={"authenticated": auth_role.role_arn}
        )





