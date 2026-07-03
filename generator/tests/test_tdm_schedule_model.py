"""Unit tests for the TDM schedule data model (stdlib ``unittest``, no third-party deps).

Run from the repo root with:

    python3 -m unittest discover -s generator/tests
"""

import copy
import json
import os
import sys
import tempfile
import unittest

# Make the generator modules importable without packaging or installation.
GEN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GEN_DIR not in sys.path:
    sys.path.insert(0, GEN_DIR)

from tdm_schedule_model import (  # noqa: E402  (import after sys.path setup)
    ScheduleValidationError,
    TimeUnit,
    load_schedule,
)

SCHEMA_PATH = os.path.join(GEN_DIR, "tdm_schedule_schema.json")
EXAMPLE_PATH = os.path.join(GEN_DIR, "example_schedule.json")


def _valid_schedule() -> dict:
    """A minimal valid schedule used as a base for negative-case mutation."""
    return {
        "name": "Test",
        "time_unit": "milliseconds",
        "tick_period": 1,
        "cycle_period": 100,
        "tasks": [
            {
                "task_name": "Task_A",
                "task_assigned_time": 2,
                "task_execution_period": 10,  # 10 ms period -> 10 ticks
                "task_execution_start_time": 0,
            }
        ],
    }


class LoadHelper(unittest.TestCase):
    """Base class providing helpers to load a dict as a schedule via a temp file."""

    def load_dict(self, data: dict):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(data, handle)
            path = handle.name
        self.addCleanup(os.unlink, path)
        return load_schedule(path, SCHEMA_PATH)

    def assert_error_contains(self, data: dict, needle: str):
        with self.assertRaises(ScheduleValidationError) as ctx:
            self.load_dict(data)
        joined = "\n".join(ctx.exception.errors)
        self.assertIn(needle, joined, msg=f"errors were:\n{joined}")
        return ctx.exception


class TestValidSchedules(LoadHelper):
    def test_example_schedule_loads(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        self.assertEqual(model.time_unit, TimeUnit.MILLISECONDS)
        self.assertEqual(model.cycle_ticks, 1000)
        self.assertEqual(model.sub_cycle_ticks, 10)
        self.assertEqual(len(model.tasks), 3)

        by_name = {t.name: t for t in model.tasks}
        t100 = by_name["Task_100Hz"]
        self.assertEqual(t100.assigned_ticks, 8)
        self.assertEqual(t100.period_ticks, 10)
        self.assertEqual(t100.executions_per_cycle, 100)
        self.assertEqual(t100.start_tick, 0)
        self.assertEqual(by_name["Task_10Hz"].start_tick, 8)

    def test_minimal_valid(self):
        model = self.load_dict(_valid_schedule())
        self.assertEqual(model.cycle_ticks, 100)
        self.assertEqual(model.tasks[0].period_ticks, 10)
        self.assertEqual(model.tasks[0].executions_per_cycle, 10)

    def test_microsecond_unit_conversion(self):
        data = _valid_schedule()
        data["time_unit"] = "microseconds"
        data["tick_period"] = 100  # 100 us tick
        data["cycle_period"] = 10000  # 100 ticks
        data["tasks"][0]["task_assigned_time"] = 1  # 1 quanta
        data["tasks"][0]["task_execution_period"] = 10  # 10 quanta
        model = self.load_dict(data)
        self.assertEqual(model.cycle_ticks, 100)
        self.assertEqual(model.tasks[0].period_ticks, 10)

    def test_fractional_tick_period(self):
        data = _valid_schedule()
        data["tick_period"] = 0.5  # 0.5 ms tick
        data["cycle_period"] = 100  # 200 ticks
        data["tasks"][0]["task_assigned_time"] = 2  # 2 quanta (used directly)
        data["tasks"][0]["task_execution_period"] = 20  # 20 quanta (used directly)
        model = self.load_dict(data)
        self.assertEqual(model.cycle_ticks, 200)
        self.assertEqual(model.tasks[0].assigned_ticks, 2)
        self.assertEqual(model.tasks[0].period_ticks, 20)

    def test_single_shot_period_zero(self):
        # A period of 0 is single-shot: the task's period is the whole cycle and it runs once.
        data = _valid_schedule()
        data["tasks"][0]["task_execution_period"] = 0
        model = self.load_dict(data)
        self.assertEqual(model.tasks[0].period_ticks, model.cycle_ticks)
        self.assertEqual(model.tasks[0].executions_per_cycle, 1)

    def test_single_shot_start_anywhere_in_cycle(self):
        # With a single-shot task the start offset may be anywhere in the cycle, not just [0, period).
        data = _valid_schedule()
        data["tasks"][0]["task_execution_period"] = 0
        data["tasks"][0]["task_execution_start_time"] = 42  # deep into the 100-tick cycle
        model = self.load_dict(data)
        self.assertEqual(model.tasks[0].start_tick, 42)


class TestStructuralValidation(LoadHelper):
    def test_unknown_time_unit(self):
        data = _valid_schedule()
        data["time_unit"] = "nanoseconds"
        self.assert_error_contains(data, "not one of")

    def test_missing_required_field(self):
        data = _valid_schedule()
        del data["cycle_period"]
        self.assert_error_contains(data, "missing required property 'cycle_period'")

    def test_additional_property_rejected(self):
        data = _valid_schedule()
        data["bogus"] = 1
        self.assert_error_contains(data, "unexpected property 'bogus'")

    def test_non_positive_tick_period(self):
        data = _valid_schedule()
        data["tick_period"] = 0
        self.assert_error_contains(data, "must be > 0")

    def test_empty_task_list(self):
        data = _valid_schedule()
        data["tasks"] = []
        self.assert_error_contains(data, "at least 1 item")

    def test_missing_start_time_rejected(self):
        data = _valid_schedule()
        del data["tasks"][0]["task_execution_start_time"]
        self.assert_error_contains(data, "missing required property 'task_execution_start_time'")


class TestSemanticValidation(LoadHelper):
    def test_assigned_time_must_be_integer_quanta(self):
        # Assigned time is a count of quanta, so a fractional value is a structural type error.
        data = _valid_schedule()
        data["tasks"][0]["task_assigned_time"] = 2.5
        self.assert_error_contains(data, "expected type 'integer'")

    def test_cycle_not_multiple_of_tick(self):
        data = _valid_schedule()
        data["tick_period"] = 3
        data["cycle_period"] = 100  # not a multiple of 3
        self.assert_error_contains(data, "cycle_period")

    def test_period_must_be_integer_quanta(self):
        # Period is a count of quanta, so a fractional value is a structural type error.
        data = _valid_schedule()
        data["tasks"][0]["task_execution_period"] = 2.5
        self.assert_error_contains(data, "expected type 'integer'")

    def test_period_does_not_divide_cycle(self):
        data = _valid_schedule()
        data["cycle_period"] = 25  # 25 ticks; period 10 does not divide 25
        self.assert_error_contains(data, "does not divide the cycle")

    def test_assigned_exceeds_period(self):
        data = _valid_schedule()
        data["tasks"][0]["task_assigned_time"] = 20  # 20 ticks > 10-tick period
        self.assert_error_contains(data, "cannot fit within its own period")

    def test_name_sanitized_to_identifier(self):
        data = _valid_schedule()
        data["tasks"][0]["task_name"] = "Task A-1"  # illegal chars -> underscores
        model = self.load_dict(data)
        self.assertEqual(model.tasks[0].name, "Task A-1")  # original preserved
        self.assertEqual(model.tasks[0].identifier, "Task_A_1")

    def test_leading_digit_prefixed(self):
        data = _valid_schedule()
        data["tasks"][0]["task_name"] = "100Hz"
        model = self.load_dict(data)
        self.assertEqual(model.tasks[0].identifier, "_100Hz")

    def test_reserved_idle_name(self):
        data = _valid_schedule()
        data["tasks"][0]["task_name"] = "Idle"
        self.assert_error_contains(data, "reserved identifier")

    def test_identifier_collision(self):
        data = _valid_schedule()
        data["tasks"] = [
            {"task_name": "Task A", "task_assigned_time": 2, "task_execution_period": 10,
             "task_execution_start_time": 0},
            {"task_name": "Task-A", "task_assigned_time": 2, "task_execution_period": 10,
             "task_execution_start_time": 0},
        ]  # both sanitize to "Task_A"
        self.assert_error_contains(data, "sanitizes to the same C identifier")

    def test_duplicate_task_names(self):
        data = _valid_schedule()
        data["tasks"].append(copy.deepcopy(data["tasks"][0]))
        self.assert_error_contains(data, "duplicate task name")

    def test_start_time_out_of_range(self):
        data = _valid_schedule()
        data["tasks"][0]["task_execution_start_time"] = 10  # == period_ticks, out of [0, 10)
        self.assert_error_contains(data, "outside the valid range")

    def test_sub_cycle_does_not_divide_cycle(self):
        data = _valid_schedule()
        data["sub_cycle_period"] = 7  # does not divide 100
        self.assert_error_contains(data, "does not divide the cycle")

    def test_over_subscribed_cycle(self):
        # Two tasks that each individually fit (assigned <= period, period divides cycle) but
        # together demand more ticks than the cycle has.
        data = _valid_schedule()
        data["cycle_period"] = 10  # 10 ticks
        data["tasks"] = [
            {"task_name": "Task_A", "task_assigned_time": 6, "task_execution_period": 10,
             "task_execution_start_time": 0},
            {"task_name": "Task_B", "task_assigned_time": 6, "task_execution_period": 10,
             "task_execution_start_time": 0},
        ]  # each: period 10 ticks, 1 exec, 6 ticks -> 12 > 10
        self.assert_error_contains(data, "over-subscribed")

    def test_errors_are_aggregated(self):
        data = _valid_schedule()
        data["tasks"][0]["task_name"] = "Idle"  # reserved-identifier error
        data["tasks"].append(
            {"task_name": "Task_B", "task_assigned_time": 3, "task_execution_period": 3,
             "task_execution_start_time": 0}
        )  # period 3 quanta does not divide the 100-quanta cycle
        exc = self.assert_error_contains(data, "reserved identifier")
        # Both problems should be reported together, not one-at-a-time.
        self.assertTrue(any("does not divide the cycle" in e for e in exc.errors))


if __name__ == "__main__":
    unittest.main()
