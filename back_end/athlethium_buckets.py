from aws_cdk import aws_s3 as s3


class athlethiumBuckets:

    def __init__(self):
        self.workoutsBucket = None

    def create_buckets(self, stack):
        self.workoutsBucket = s3.Bucket(
            stack, "workoutsBucket",
            bucket_name="athlethium-workouts"
        )
        return self







