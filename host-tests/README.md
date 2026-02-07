# TDM Scheduler Test Framework

This directory contains the CppUTest testing framework setup for the TDM Scheduler project.

## Structure

```
host-tests/
├── CMakeLists.txt      # CMake configuration for building tests
├── Dockerfile          # Docker environment for testing
├── docker-compose.yml  # Docker Compose configuration
├── run_tests.sh        # Linux/Mac test runner script
├── run_tests.bat       # Windows test runner script
├── README.md           # This file
└── tests/
    ├── AllTests.cpp    # Main test runner
    └── ExampleTest.cpp # Example test cases
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Run tests automatically:**
   ```bash
   docker-compose up test-runner
   ```

2. **Interactive development:**
   ```bash
   docker-compose up cpputest
   # This opens an interactive bash shell in the container
   ```

### Using Scripts

**On Windows:**
```cmd
run_tests.bat
```

**On Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Manual Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t tdm-scheduler-tests -f Dockerfile ..
   ```

2. **Run tests:**
   ```bash
   docker run --rm -v "$(pwd)/..:/workspace" -w /workspace/host-tests tdm-scheduler-tests bash -c "
     mkdir -p build &&
     cd build &&
     cmake .. &&
     make &&
     ./tdm_tests -v
   "
   ```

## Adding New Tests

1. Create a new `.cpp` file in the `tests/` directory
2. Include the CppUTest header: `#include "CppUTest/TestHarness.h"`
3. Define test groups and tests:

```cpp
#include "CppUTest/TestHarness.h"

TEST_GROUP(MyModuleTests)
{
    void setup()
    {
        // Setup code before each test
    }

    void teardown()
    {
        // Teardown code after each test
    }
};

TEST(MyModuleTests, SomeFeatureTest)
{
    // Your test code here
    CHECK_EQUAL(expected, actual);
    CHECK_TRUE(condition);
    STRCMP_EQUAL("expected", "actual");
}
```

## Testing Your Source Code

The CMakeLists.txt is configured to automatically include source files from `../src/`. Make sure to:

1. Place your source code in the `src/` directory at the project root
2. Avoid having multiple `main()` functions (the test runner provides main)
3. Create header files for functions you want to test

## Available Test Macros

- `CHECK(condition)` - Check boolean condition
- `CHECK_TRUE(condition)` - Check true condition
- `CHECK_FALSE(condition)` - Check false condition
- `CHECK_EQUAL(expected, actual)` - Check equality
- `STRCMP_EQUAL(expected, actual)` - Check string equality
- `DOUBLES_EQUAL(expected, actual, tolerance)` - Check floating point equality
- `FAIL(message)` - Explicitly fail with message

## Debugging

To debug tests in the Docker container:

```bash
docker run -it --rm -v "$(pwd)/..:/workspace" -w /workspace/host-tests/build tdm-scheduler-tests bash
# Then use gdb: gdb ./tdm_tests
```

## Code Coverage

The Docker image includes gcov and lcov for code coverage analysis. You can generate coverage reports by modifying the CMakeLists.txt to include coverage flags.