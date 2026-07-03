@echo off
REM Build and run tests script for TDM Scheduler (Windows)

echo 🔨 Building Docker image...
docker build -t tdm-scheduler-tests -f Dockerfile ..
if errorlevel 1 goto :error

echo 📦 Creating build directory...
docker run --rm -v "%cd%\..:/workspace" tdm-scheduler-tests bash -c "mkdir -p /workspace/tests/build"
if errorlevel 1 goto :error

echo ⚙️ Running CMake configuration...
docker run --rm -v "%cd%\..:/workspace" -w /workspace/tests/build tdm-scheduler-tests cmake ..
if errorlevel 1 goto :error

echo 🔧 Building tests...
docker run --rm -v "%cd%\..:/workspace" -w /workspace/tests/build tdm-scheduler-tests make
if errorlevel 1 goto :error

echo 🧪 Running tests...
docker run --rm -v "%cd%\..:/workspace" -w /workspace/tests/build tdm-scheduler-tests ./tdm_tests -v
if errorlevel 1 goto :error

echo ✅ Tests completed!
goto :end

:error
echo ❌ An error occurred during the test process!
exit /b 1

:end