from aws_cdk import (
    Stack, CfnOutput,
    aws_cognito as _cognito,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigw,
    RemovalPolicy
)
from constructs import Construct
from .athlethium_buckets import athlethiumBuckets
from .athlethium_cognito import athlethiumCognito
from .athlethium_databases import athlethiumDB
from .athlethium_lambdas import athlethiumLambdas
from .athlethium_api import athlethiumAPI

class BackEndStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tables = athlethiumDB()
        tables.create_dbs(self)

        cognito = athlethiumCognito()
        cognito.create_cognito(self)

        lambdas = athlethiumLambdas()
        lambdas.create_lambdas(self, tables, cognito)

        buckets = athlethiumBuckets().create_buckets(self)

        api = athlethiumAPI().create_api(self, cognito.user_pool, lambdas)

        CfnOutput(self, "APIEndpoint", value=api.url)
        CfnOutput(self, "UserPoolId", value=cognito.user_pool.user_pool_id)
        CfnOutput(self,"AppClientId",value=cognito.app_client.user_pool_client_id)
        CfnOutput(self,"IdentityPoolId",value=cognito.identity_pool.ref)

