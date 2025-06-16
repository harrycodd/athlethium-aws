from aws_cdk import aws_s3 as s3


class athlethiumBuckets:

    def __init__(self):
        self.workoutsBucket = None

    def create_buckets(self, stack):
        # Create new S3 buckets (use this if buckets don't exist yet)
        self.workoutsBucket = s3.Bucket(
            stack, "workoutsBucket",
            bucket_name="athlethium-workouts"
        )
        
        # Return self to allow chaining and assignment
        return self







