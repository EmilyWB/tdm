#!/bin/bash

# Build and run tests script for TDM Scheduler

set -e

echo "🔨 Building Docker image..."
docker build -t tdm-scheduler-tests -f Dockerfile ..

echo "📦 Creating build directory..."
docker run --rm -v "$(pwd)/..:/workspace" tdm-scheduler-tests bash -c "mkdir -p /workspace/tests/build"

echo "⚙️ Running CMake configuration..."
docker run --rm -v "$(pwd)/..:/workspace" -w /workspace/tests/build tdm-scheduler-tests cmake ..

echo "🔧 Building tests..."
docker run --rm -v "$(pwd)/..:/workspace" -w /workspace/tests/build tdm-scheduler-tests make

echo "🧪 Running tests..."
docker run --rm -v "$(pwd)/..:/workspace" -w /workspace/tests/build tdm-scheduler-tests ./tdm_tests -v

echo "✅ Tests completed!"