# Use Ubuntu as base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    gdb \
    valgrind \
    gcov \
    lcov \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy the entire project
COPY . /workspace/

# Set the working directory to tests
WORKDIR /workspace/tests

# Create build directory
RUN mkdir -p build

# Default command
CMD ["bash"]