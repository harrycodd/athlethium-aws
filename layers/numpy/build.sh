#!/bin/bash
# Build script for NumPy layer

LAYER_DIR="$(dirname "$0")"
cd "$LAYER_DIR"

# Clean previous build
rm -rf python/

# Create python directory
mkdir -p python

# Install dependencies using Docker to match Lambda environment
if command -v docker &> /dev/null; then
    echo "Using Docker to build layer for Lambda environment..."
    docker run --rm -v "$(pwd)":/var/task -w /var/task public.ecr.aws/lambda/python:3.11 \
        pip install -r requirements.txt -t python/
else
    echo "Docker not found, installing locally (may not be compatible with Lambda)..."
    pip install -r requirements.txt -t python/ --platform linux_x86_64 --only-binary=all
fi

echo "NumPy layer built successfully!"
