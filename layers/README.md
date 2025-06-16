# Lambda Layers

This directory contains AWS Lambda layers for the Athlethium backend.

## Available Layers

### NumPy Layer
- **Path**: `layers/numpy/`
- **Contents**: NumPy 1.26.4 for scientific computing
- **CDK Class**: `NumpyLayer` in `back_end/cdk_numpy_layer.py`

### Anthropic Layer
- **Path**: `layers/anthropic/`
- **Contents**: Anthropic SDK 0.34.0 for AI capabilities
- **CDK Class**: `AnthropicLayer` in `back_end/cdk_anthropic_layer.py`

## Building Layers

To rebuild the layers (e.g., when updating dependencies):

```bash
# For NumPy layer
cd layers/numpy
pip install -r requirements.txt -t python/

# For Anthropic layer
cd layers/anthropic
pip install -r requirements.txt -t python/
```

## Using Layers in Lambda Functions

Both layers are automatically attached to all Lambda functions created through the `athlethium_lambdas.py` module.

To use NumPy in your Lambda function:
```python
import numpy as np
```

To use Anthropic SDK in your Lambda function:
```python
from anthropic import Anthropic
```

## Layer Structure

Each layer follows the AWS Lambda layer structure:
```
layer_name/
├── requirements.txt    # Package dependencies
├── build.sh           # Build script (optional)
└── python/            # Installed packages (created during build)
    └── package_name/   # Actual Python packages
```

## Notes

- Layers are compatible with Python 3.9, 3.10, 3.11, and 3.12 runtimes
- The layers are built for Linux x86_64 architecture to match Lambda environment
- Total unzipped size of all layers must not exceed 250MB per function
