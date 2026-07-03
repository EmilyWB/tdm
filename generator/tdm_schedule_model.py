"""Canonical, tick-based internal representation of a TDM schedule.

This module owns how a schedule JSON file is *interpreted*, *validated*, and *represented*
internally, prior to any code generation. Everything is canonicalized to integer **ticks**
because the scheduler is tick-indexed (``kScheduleTable[timeQuanta]``); the floats in the JSON
are human-friendly inputs expressed in ``time_unit``.

Dependency-free: standard library only (``json``, ``enum``, ``re``, ``dataclasses``, ``fractions``).
Structural (JSON Schema) validation is delegated to :mod:`tdm_schema_validator`; this module adds
the semantic/domain rules that JSON Schema cannot express (tick divisibility, feasibility, C
identifier rules, ...).

Placement of tasks into concrete tick slots (the ``kScheduleTable`` contents) and auto-computing an
omitted ``start_tick`` are deliberately *not* done here — those belong to the generation phase and
will consume the :class:`ScheduleModel` produced by :func:`load_schedule`.
"""

from __future__ import annotations

import enum
import json
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Tuple

from tdm_schema_validator import validate_schema

# Any character that is not legal in a C identifier is replaced with ``_``.
_NON_IDENTIFIER_CHARS = re.compile(r"[^A-Za-z0-9_]")

# ``tdmTaskId_Idle`` is always emitted first and is reserved.
_RESERVED_IDENTIFIERS = frozenset({"Idle"})


def _sanitize_identifier(name: str) -> str:
    """Derive a C identifier from a task name.

    Non-identifier characters become ``_`` and a leading digit is prefixed with ``_``. Returns
    an empty string if no identifier can be derived (e.g. an empty name), which the caller treats
    as an error.
    """
    identifier = _NON_IDENTIFIER_CHARS.sub("_", name)
    if identifier and identifier[0].isdigit():
        identifier = "_" + identifier
    return identifier


class ScheduleValidationError(Exception):
    """Raised when a schedule fails structural or semantic validation.

    Carries the full list of problems (validate-all, not fail-fast) so the user can fix
    everything in one pass rather than one error at a time.
    """

    def __init__(self, errors: List[str]):
        self.errors = list(errors)
        super().__init__(
            "schedule is invalid:\n" + "\n".join(f"  - {e}" for e in self.errors)
        )


class TimeUnit(enum.Enum):
    MICROSECONDS = "microseconds"
    MILLISECONDS = "milliseconds"
    SECONDS = "seconds"

    @property
    def units_per_second(self) -> int:
        return {
            "microseconds": 1_000_000,
            "milliseconds": 1_000,
            "seconds": 1,
        }[self.value]


@dataclass(frozen=True)
class TaskModel:
    """A single task, canonicalized to integer ticks."""

    name: str  # original task_name, kept for comments/metadata
    identifier: str  # sanitized C identifier -> tdmTaskId_<identifier>
    assigned_ticks: int  # ticks occupied by one execution
    period_ticks: int  # ticks between successive executions (== cycle_ticks for single-shot)
    executions_per_cycle: int  # cycle_ticks / period_ticks (1 for single-shot)
    start_tick: int  # first-execution offset (required in the JSON)


@dataclass(frozen=True)
class ScheduleModel:
    """A fully validated schedule in canonical (tick-based) form."""

    name: str
    description: str
    time_unit: TimeUnit
    tick_period: float
    cycle_period: float
    sub_cycle_period: Optional[float]
    cycle_ticks: int  # == kCycleSize
    sub_cycle_ticks: Optional[int]
    tasks: Tuple[TaskModel, ...]


def _ticks(value_units, tick_period, label: str, errors: List[str]) -> Optional[int]:
    """Convert a duration in ``time_unit`` to integer ticks.

    Returns the tick count if ``value_units`` is an exact multiple of ``tick_period``, otherwise
    records an error and returns ``None``. Uses exact rational arithmetic via ``Fraction`` so there
    is no floating-point tolerance to tune.
    """
    ratio = Fraction(str(value_units)) / Fraction(str(tick_period))
    if ratio.denominator != 1:
        errors.append(
            f"{label}: {value_units} is not an exact multiple of tick_period {tick_period}"
        )
        return None
    return int(ratio)




def _build_task(index: int, raw: dict, identifier: str, name_ok: bool,
                cycle_ticks: Optional[int], errors: List[str]) -> Optional[TaskModel]:
    path = f"tasks[{index}]"
    ok = name_ok

    # Assigned time and start offset are counts of time quanta (ticks), used directly — not
    # durations. Schema validation already guarantees they are integers (assigned >= 1, start >= 0).
    assigned_ticks = raw["task_assigned_time"]

    # Period is a count of quanta (ticks), used directly. A period of 0 is single-shot: the task
    # runs exactly once per cycle, so its period is the whole cycle.
    raw_period = raw["task_execution_period"]
    if raw_period == 0:
        period_ticks = cycle_ticks  # may be None if cycle_period was itself invalid
    else:
        period_ticks = raw_period  # integer >= 1 per schema

    if period_ticks is not None and assigned_ticks > period_ticks:
        errors.append(
            f"{path}: assigned_ticks ({assigned_ticks}) exceeds the execution period "
            f"({period_ticks} ticks) — task cannot fit within its own period"
        )
        ok = False

    if period_ticks is not None and cycle_ticks is not None and cycle_ticks % period_ticks != 0:
        errors.append(
            f"{path}: execution period ({period_ticks} ticks) does not divide the cycle "
            f"({cycle_ticks} ticks) a whole number of times"
        )
        ok = False

    start_tick = raw["task_execution_start_time"]
    if period_ticks is not None and not (0 <= start_tick < period_ticks):
        errors.append(
            f"{path}.task_execution_start_time: {start_tick} ticks is outside the valid "
            f"range [0, {period_ticks})"
        )
        ok = False

    if not ok or period_ticks is None:
        return None

    executions_per_cycle = cycle_ticks // period_ticks if cycle_ticks is not None else 0
    return TaskModel(
        name=raw["task_name"],
        identifier=identifier,
        assigned_ticks=assigned_ticks,
        period_ticks=period_ticks,
        executions_per_cycle=executions_per_cycle,
        start_tick=start_tick,
    )


def _build_model(data: dict, errors: List[str]) -> Optional[ScheduleModel]:
    time_unit = TimeUnit(data["time_unit"])  # enum already validated structurally
    tick_period = data["tick_period"]
    cycle_period = data["cycle_period"]

    cycle_ticks = _ticks(cycle_period, tick_period, "cycle_period", errors)
    if cycle_ticks is not None and cycle_ticks < 1:
        errors.append("cycle_period: must be at least one tick")
        cycle_ticks = None

    sub_cycle_period = data.get("sub_cycle_period")
    sub_cycle_ticks: Optional[int] = None
    if sub_cycle_period is not None:
        sub_cycle_ticks = _ticks(sub_cycle_period, tick_period, "sub_cycle_period", errors)
        if sub_cycle_ticks is not None and cycle_ticks is not None and cycle_ticks % sub_cycle_ticks != 0:
            errors.append(
                f"sub_cycle_period: {sub_cycle_ticks} ticks does not divide the cycle "
                f"({cycle_ticks} ticks) a whole number of times"
            )

    tasks: List[TaskModel] = []
    seen_names = set()
    identifier_sources = {}  # sanitized identifier -> original name that first produced it
    for index, raw in enumerate(data["tasks"]):
        name = raw["task_name"]
        path = f"tasks[{index}]"
        name_ok = True

        if name in seen_names:
            errors.append(f"{path}.task_name: duplicate task name {name!r}")
            name_ok = False
        seen_names.add(name)

        identifier = _sanitize_identifier(name)
        if not identifier:
            errors.append(f"{path}.task_name: {name!r} cannot be converted to a C identifier")
            name_ok = False
        elif identifier in _RESERVED_IDENTIFIERS:
            errors.append(
                f"{path}.task_name: {name!r} maps to the reserved identifier {identifier!r}"
            )
            name_ok = False
        elif identifier in identifier_sources:
            errors.append(
                f"{path}.task_name: {name!r} sanitizes to the same C identifier {identifier!r} "
                f"as {identifier_sources[identifier]!r}"
            )
            name_ok = False
        else:
            identifier_sources[identifier] = name

        task = _build_task(
            index, raw, identifier, name_ok, cycle_ticks, errors
        )
        if task is not None:
            tasks.append(task)

    # Utilization: a necessary (not sufficient) feasibility check. Full per-tick conflict
    # detection is a placement/generation concern.
    if cycle_ticks is not None and len(tasks) == len(data["tasks"]):
        used = sum(t.assigned_ticks * t.executions_per_cycle for t in tasks)
        if used > cycle_ticks:
            errors.append(
                f"schedule is over-subscribed: tasks require {used} ticks per cycle but only "
                f"{cycle_ticks} are available"
            )

    if errors:
        return None

    return ScheduleModel(
        name=data["name"],
        description=data.get("description", ""),
        time_unit=time_unit,
        tick_period=tick_period,
        cycle_period=cycle_period,
        sub_cycle_period=sub_cycle_period,
        cycle_ticks=cycle_ticks,
        sub_cycle_ticks=sub_cycle_ticks,
        tasks=tuple(tasks),
    )


def load_schedule(json_path: str, schema_path: str) -> ScheduleModel:
    """Load, validate, and canonicalize a schedule JSON file into a :class:`ScheduleModel`.

    Raises :class:`ScheduleValidationError` (with the aggregated list of problems) if the file is
    structurally or semantically invalid.
    """
    with open(json_path, "r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ScheduleValidationError([f"{json_path}: invalid JSON: {exc}"])

    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)

    # Structural errors are fatal: the semantic pass assumes the shapes/types are trustworthy.
    structural = validate_schema(data, schema)
    if structural:
        raise ScheduleValidationError(structural)

    errors: List[str] = []
    model = _build_model(data, errors)
    if model is None:
        raise ScheduleValidationError(errors)
    return model
