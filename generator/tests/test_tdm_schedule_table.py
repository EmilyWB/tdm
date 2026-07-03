"""Unit tests for schedule-table placement (stdlib ``unittest``, no third-party deps).

Run from the repo root with:

    python3 -m unittest discover -s generator/tests
"""

import os
import sys
import unittest

# Make the generator modules importable without packaging or installation.
GEN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GEN_DIR not in sys.path:
    sys.path.insert(0, GEN_DIR)

from tdm_schedule_model import (  # noqa: E402  (import after sys.path setup)
    ScheduleModel,
    TaskModel,
    TimeUnit,
    load_schedule,
)
from tdm_schedule_table import (  # noqa: E402
    TableGenerationError,
    build_schedule_table,
)

SCHEMA_PATH = os.path.join(GEN_DIR, "tdm_schedule_schema.json")
EXAMPLE_PATH = os.path.join(GEN_DIR, "example_schedule.json")


def _task(identifier, assigned, period, executions, start):
    return TaskModel(
        name=identifier,
        identifier=identifier,
        assigned_ticks=assigned,
        period_ticks=period,
        executions_per_cycle=executions,
        start_tick=start,
    )


def _model(cycle_ticks, tasks):
    return ScheduleModel(
        name="Test",
        description="",
        time_unit=TimeUnit.MILLISECONDS,
        tick_period=1,
        cycle_period=cycle_ticks,
        sub_cycle_period=None,
        cycle_ticks=cycle_ticks,
        sub_cycle_ticks=None,
        tasks=tuple(tasks),
    )


class TestExplicitPlacement(unittest.TestCase):
    def test_single_task_placed_contiguously_each_period(self):
        # assigned 2, period 5, 2 executions over a 10-tick cycle, starting at 0.
        model = _model(10, [_task("A", assigned=2, period=5, executions=2, start=0)])
        table = build_schedule_table(model)
        self.assertEqual(
            table,
            ["A", "A", None, None, None, "A", "A", None, None, None],
        )

    def test_start_offset_shifts_the_window(self):
        model = _model(10, [_task("A", assigned=2, period=5, executions=2, start=1)])
        table = build_schedule_table(model)
        self.assertEqual(
            table,
            [None, "A", "A", None, None, None, "A", "A", None, None],
        )

    def test_two_non_overlapping_tasks_coexist(self):
        model = _model(
            10,
            [
                _task("A", assigned=2, period=10, executions=1, start=0),
                _task("B", assigned=2, period=10, executions=1, start=2),
            ],
        )
        table = build_schedule_table(model)
        self.assertEqual(table[:4], ["A", "A", "B", "B"])


class TestConflicts(unittest.TestCase):
    def test_overlapping_explicit_tasks_conflict(self):
        model = _model(
            10,
            [
                _task("A", assigned=2, period=10, executions=1, start=0),
                _task("B", assigned=2, period=10, executions=1, start=1),  # overlaps A at tick 1
            ],
        )
        with self.assertRaises(TableGenerationError) as ctx:
            build_schedule_table(model)
        joined = "\n".join(ctx.exception.errors)
        self.assertIn("tick 1", joined)
        self.assertIn("A", joined)
        self.assertIn("B", joined)

    def test_all_conflicting_ticks_reported(self):
        model = _model(
            4,
            [
                _task("A", assigned=4, period=4, executions=1, start=0),  # ticks 0-3
                _task("B", assigned=4, period=4, executions=1, start=0),  # ticks 0-3, all clash
            ],
        )
        with self.assertRaises(TableGenerationError) as ctx:
            build_schedule_table(model)
        conflict_lines = [e for e in ctx.exception.errors if "conflict" in e]
        self.assertEqual(len(conflict_lines), 4)  # one per tick


class TestFromExample(unittest.TestCase):
    def test_example_schedule_builds(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        table = build_schedule_table(model)
        self.assertEqual(len(table), 1000)
        # Task_100Hz (assigned 8, start 0) owns ticks 0-7 of each 10-tick block.
        self.assertEqual(table[0:8], ["Task_100Hz"] * 8)
        # Task_10Hz and Task_1Hz start at ticks 8 and 9 (the two free ticks of the first block).
        self.assertEqual(table[8], "Task_10Hz")
        self.assertEqual(table[9], "Task_1Hz")


if __name__ == "__main__":
    unittest.main()
