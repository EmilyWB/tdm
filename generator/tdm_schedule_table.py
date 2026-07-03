"""Placement of validated tasks into the tick-indexed schedule table (``kScheduleTable``).

Consumes a validated :class:`~tdm_schedule_model.ScheduleModel` and walks each task across the
cycle: one execution every ``period_ticks``, starting at its JSON-provided ``start_tick``,
occupying ``assigned_ticks`` consecutive ticks. Each occupied tick is stamped with the task's
identifier. Placement is fully determined by the JSON — there is no packing or auto-placement.

If, after placement, any tick is claimed by more than one task, the schedule is over-constrained
and cannot be realized: that is a :class:`TableGenerationError`. During building each tick holds a
*list* of the tasks landing on it (so a conflict can be reported with every task involved, matching
the mental model of "a table cell that becomes a list when two or more tasks collide").

Dependency-free: standard library only.
"""

from __future__ import annotations

from typing import List, Optional

from tdm_schedule_model import ScheduleModel, TaskModel


class TableGenerationError(Exception):
    """Raised when validated tasks cannot be placed into a conflict-free schedule table.

    Carries the full list of problems (validate-all, not fail-fast) so the user sees every
    conflict / unplaceable task at once.
    """

    def __init__(self, errors: List[str]):
        self.errors = list(errors)
        super().__init__(
            "cannot generate schedule table:\n" + "\n".join(f"  - {e}" for e in self.errors)
        )


def _execution_ticks(task: TaskModel, cycle_ticks: int, start_tick: int) -> List[int]:
    """Every tick index occupied by ``task`` over one cycle if it starts at ``start_tick``.

    Executions repeat every ``period_ticks``; each occupies ``assigned_ticks`` consecutive ticks.
    Indices are taken modulo ``cycle_ticks`` so an execution window that runs past the end of the
    cycle wraps around to the start.
    """
    ticks: List[int] = []
    for execution in range(task.executions_per_cycle):
        base = start_tick + execution * task.period_ticks
        for offset in range(task.assigned_ticks):
            ticks.append((base + offset) % cycle_ticks)
    return ticks


def build_schedule_table(model: ScheduleModel) -> List[Optional[str]]:
    """Place every task into the cycle and return the tick-indexed table.

    The result has length ``model.cycle_ticks``; each element is the identifier of the task that
    owns that tick, or ``None`` for an idle tick (which the generator emits as ``tdmTaskId_Idle``).

    Raises :class:`TableGenerationError` if two tasks conflict on a tick.
    """
    cycle_ticks = model.cycle_ticks
    occupants: List[List[str]] = [[] for _ in range(cycle_ticks)]
    errors: List[str] = []

    for task in model.tasks:
        for tick in _execution_ticks(task, cycle_ticks, task.start_tick):
            occupants[tick].append(task.identifier)

    for tick, names in enumerate(occupants):
        if len(names) > 1:
            involved = ", ".join(sorted(set(names)))
            errors.append(f"tick {tick}: scheduling conflict between tasks {involved}")

    if errors:
        raise TableGenerationError(errors)

    return [names[0] if names else None for names in occupants]
