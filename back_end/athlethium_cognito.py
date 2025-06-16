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
            # Do NOT set sign_in_aliases or sign_in_case_sensitive to avoid UsernameConfiguration update errors
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
                email_subject="Welcome to Athlethium!",
                email_body="Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE
            ),
            user_invitation=cognito.UserInvitationConfig(
                email_subject="You are invited to Athlethium!",
                email_body="Your temporary password is {####}. Your username is {username}."
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        self.app_client = self.user_pool.add_client(
            "athlethiumAppClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user=True,
                user_password=True
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





