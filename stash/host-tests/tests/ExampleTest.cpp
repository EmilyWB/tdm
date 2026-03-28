#include "CppUTest/TestHarness.h"

TEST_GROUP(ExampleTests)
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

TEST(ExampleTests, FirstTest)
{
    CHECK_EQUAL(1, 1);
    CHECK_TRUE(true);
    STRCMP_EQUAL("hello", "hello");
}

TEST(ExampleTests, BasicMath)
{
    int result = 2 + 2;
    CHECK_EQUAL(4, result);
}

TEST(ExampleTests, StringTest)
{
    const char* expected = "TDM Scheduler";
    const char* actual = "TDM Scheduler";
    STRCMP_EQUAL(expected, actual);
}