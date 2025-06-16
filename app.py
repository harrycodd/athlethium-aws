#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import App, Environment

from back_end.back_end_stack import BackEndStack


app = App()
BackEndStack(
    app, "BackEndStack",
    env=Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region="eu-west-2"
    )
)

app.synth()
