import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from aws_cdk import (
    aws_lambda as _lambda,
    BundlingOptions,
    DockerImage,
)
from constructs import Construct


class NumpyLayer(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Use pre-built layer directory with packages already installed
        layer_path = Path(__file__).parent.parent / "layers" / "numpy"
        
        self.layer = _lambda.LayerVersion(
            self,
            "NumpyLayerVersion",
            layer_version_name="numpy-layer",
            description="NumPy layer for Lambda functions",
            code=_lambda.Code.from_asset(str(layer_path)),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_9,
                _lambda.Runtime.PYTHON_3_10,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_12,
            ],
        )
