"""Unit tests for C++ token generation (stdlib ``unittest``, no third-party deps).

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
from tdm_schedule_generation import (  # noqa: E402
    GenerationError,
    GeneratorOptions,
    build_token_map,
    render_execution_calls,
    render_scheduling_table,
    render_task_data,
    render_task_id_typedef,
    render_template,
)

SCHEMA_PATH = os.path.join(GEN_DIR, "tdm_schedule_schema.json")
EXAMPLE_PATH = os.path.join(GEN_DIR, "example_schedule.json")
STUB_DIR = os.path.normpath(os.path.join(GEN_DIR, "..", "src", "stubs"))


def _task(identifier, assigned, period, executions, start):
    return TaskModel(
        name=identifier,
        identifier=identifier,
        assigned_ticks=assigned,
        period_ticks=period,
        executions_per_cycle=executions,
        start_tick=start,
    )


def _model(cycle_ticks, tasks, sub_cycle_ticks=None):
    return ScheduleModel(
        name="Test",
        description="",
        time_unit=TimeUnit.MILLISECONDS,
        tick_period=1,
        cycle_period=cycle_ticks,
        sub_cycle_period=sub_cycle_ticks,
        cycle_ticks=cycle_ticks,
        sub_cycle_ticks=sub_cycle_ticks,
        tasks=tuple(tasks),
    )


class TestRenderers(unittest.TestCase):
    def test_task_id_typedef(self):
        model = _model(10, [_task("A", 2, 5, 2, 0), _task("B", 1, 10, 1, 4)])
        self.assertEqual(
            render_task_id_typedef(model),
            "    tdmTaskId_A,\n    tdmTaskId_B,",
        )

    def test_execution_calls_dispatch_and_reset(self):
        model = _model(10, [_task("A", 2, 5, 2, 0)])
        block = render_execution_calls(model)
        self.assertIn("case (tdmTaskId_A): {", block)
        self.assertIn("setCurrentExecutingTask(tdmTaskId_A);", block)
        self.assertIn("taskFunction_A();", block)
        self.assertIn("setCurrentExecutingTask(tdmTaskId_Idle);", block)
        self.assertIn("break;", block)

    def test_task_data_one_entry_per_task(self):
        model = _model(10, [_task("A", 2, 5, 2, 0), _task("B", 1, 10, 1, 4)])
        data = render_task_data(model)
        self.assertEqual(len(data.splitlines()), 2)
        self.assertIn("{ tdmTaskId_A }", data)
        self.assertIn("{ tdmTaskId_B }", data)

    def test_scheduling_table_maps_idle_and_wraps_rows(self):
        # A owns ticks 0-1, everything else idle; width 5 -> two rows of a 10-tick cycle.
        table = ["A", "A", None, None, None, None, None, None, None, None]
        rendered = render_scheduling_table(table, row_width=5)
        lines = rendered.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("/* tick 0 */", lines[0])
        self.assertIn("/* tick 5 */", lines[1])
        self.assertEqual(lines[0].count("tdmTaskId_A"), 2)
        self.assertIn("tdmTaskId_Idle", lines[0])


class TestTemplateSubstitution(unittest.TestCase):
    def test_block_token_preserves_indentation(self):
        template = "x\n    !<BODY>!\ny"
        out = render_template(template, {"BODY": "if (a) {\n    b();\n}"})
        # Every rendered line is prefixed with the placeholder line's 4-space indent.
        self.assertEqual(out, "x\n    if (a) {\n        b();\n    }\ny")

    def test_inline_token_replaced(self):
        out = render_template("size = !<N>!;", {"N": "1000"})
        self.assertEqual(out, "size = 1000;")

    def test_unrecognized_token_raises(self):
        with self.assertRaises(GenerationError) as ctx:
            render_template("a !<UNKNOWN>! b", {"KNOWN": "x"})
        self.assertIn("UNKNOWN", str(ctx.exception))

    def test_empty_value_leaves_no_trailing_whitespace(self):
        out = render_template('#include "!<PATH>!tdm.hpp"', {"PATH": ""})
        self.assertEqual(out, '#include "tdm.hpp"')


class TestOptions(unittest.TestCase):
    def test_invalid_schedule_type_rejected(self):
        model = _model(10, [_task("A", 2, 5, 2, 0)])
        with self.assertRaises(GenerationError):
            build_token_map(model, GeneratorOptions(schedule_type="bogus"))

    def test_schedule_type_maps_to_enum(self):
        model = _model(10, [_task("A", 2, 5, 2, 0)])
        tokens = build_token_map(model, GeneratorOptions(schedule_type="json"))
        self.assertEqual(tokens["SCHEDULE_TYPE"], "tdmScheduleType_json")


class TestEndToEnd(unittest.TestCase):
    def test_real_stubs_fully_substituted(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        tokens = build_token_map(model, GeneratorOptions(profiler_namespace="prof"))
        for stub_name in ("tdm_stub.hpp", "tdm_stub.cpp"):
            with open(os.path.join(STUB_DIR, stub_name), "r", encoding="utf-8") as handle:
                rendered = render_template(handle.read(), tokens)
            # No placeholder should survive.
            self.assertNotIn("!<", rendered, msg=f"unsubstituted token left in {stub_name}")

    def test_number_of_tasks_matches_count(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        tokens = build_token_map(model, GeneratorOptions())
        self.assertEqual(tokens["NUMBER_OF_TASKS"], "3")

    def test_cycle_size_and_table_length_agree(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        tokens = build_token_map(model, GeneratorOptions())
        self.assertEqual(tokens["CYCLE_SIZE"], "1000")
        # One table entry per tick: 1000 entries laid out in rows of the 10-tick sub-cycle.
        entries = tokens["SCHEDULING_TABLE"].count("tdmTaskId_")
        self.assertEqual(entries, 1000)

    def test_first_block_places_expected_tasks(self):
        model = load_schedule(EXAMPLE_PATH, SCHEMA_PATH)
        first_row = build_token_map(model, GeneratorOptions())["SCHEDULING_TABLE"].splitlines()[0]
        # Task_100Hz owns ticks 0-7, Task_10Hz tick 8, Task_1Hz tick 9.
        self.assertEqual(first_row.count("tdmTaskId_Task_100Hz"), 8)
        self.assertIn("tdmTaskId_Task_10Hz", first_row)
        self.assertIn("tdmTaskId_Task_1Hz", first_row)


if __name__ == "__main__":
    unittest.main()
