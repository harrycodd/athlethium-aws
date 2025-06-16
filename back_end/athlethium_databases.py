from aws_cdk import (
    aws_dynamodb as dynamodb
)


class athlethiumDB:
    def __init__(self):
        self.userTable = None
        self.dailyMetrics = None
        self.trainingSchedule = None
        self.workoutsTable = None

    def create_dbs(self, stack):
        self.userTable = dynamodb.Table(
            stack, "userTable",
            table_name="userTable",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        self.dailyMetrics = dynamodb.Table(
            stack, "dailyMetrics",
            table_name="dailyMetrics",
            partition_key=dynamodb.Attribute(
                name="metricId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        self.trainingSchedule = dynamodb.Table(
            stack, "trainingSchedule",
            table_name="trainingSchedule",
            partition_key=dynamodb.Attribute(
                name="scheduleId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        self.workoutsTable = dynamodb.Table(
            stack, "workoutsTable",
            table_name="workoutsTable",
            partition_key=dynamodb.Attribute(
                name="workoutId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )


