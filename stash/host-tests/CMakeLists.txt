cmake_minimum_required(VERSION 3.8)

project(TDMSchedulerTests
    VERSION 1.0.0
    LANGUAGES CXX C
)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include CppUTest
add_subdirectory(${CMAKE_SOURCE_DIR}/../lib/cpputest cpputest_build)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/../src
    ${CMAKE_SOURCE_DIR}/../lib/cpputest/include
)

# Collect all test files
file(GLOB_RECURSE TEST_SOURCES
    "tests/*.cpp"
    "tests/*.c"
)

# Collect source files to test (excluding main.cpp if it exists)
file(GLOB_RECURSE SRC_FILES
    "${CMAKE_SOURCE_DIR}/../src/*.cpp"
    "${CMAKE_SOURCE_DIR}/../src/*.c"
)

# Remove any main.cpp files from source files
list(FILTER SRC_FILES EXCLUDE REGEX ".*main\\.cpp$")

# Create test executable
if(TEST_SOURCES)
    add_executable(tdm_tests
        ${TEST_SOURCES}
        ${SRC_FILES}
    )

    # Link CppUTest libraries
    target_link_libraries(tdm_tests
        CppUTest
        CppUTestExt
    )

    # Set compiler flags for testing
    target_compile_options(tdm_tests PRIVATE
        $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -g>
        $<$<CXX_COMPILER_ID:MSVC>:/W4>
    )

    # Enable testing
    enable_testing()
    add_test(NAME AllTests COMMAND tdm_tests -v)
else()
    message(WARNING "No test files found in tests/ directory")
endif()

# Custom target to run tests
add_custom_target(run_tests
    COMMAND tdm_tests -v
    DEPENDS tdm_tests
    COMMENT "Running all tests"
)

# Print configuration info
message(STATUS "CppUTest found at: ${CMAKE_SOURCE_DIR}/../lib/cpputest")
message(STATUS "Source directory: ${CMAKE_SOURCE_DIR}/../src")
message(STATUS "Test sources: ${TEST_SOURCES}")