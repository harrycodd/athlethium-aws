from aws_cdk import aws_lambda as _lambda
from constructs import Construct
import os
from pathlib import Path

class NumpyLayer(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get the path to the numpy layer directory
        layer_path = str(Path(__file__).resolve().parent.parent / "layers" / "numpy")
        
        self.layer = _lambda.LayerVersion(
            self, "NumpyLayerVersion",
            code=_lambda.Code.from_asset(layer_path),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_9,
                _lambda.Runtime.PYTHON_3_10,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_12
            ],
            description="NumPy layer for Lambda functions",
            layer_version_name="numpy-layer"
        )
