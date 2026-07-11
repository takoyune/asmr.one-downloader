from typing import Protocol, Any, Optional
from rich.progress import Progress, TaskID

class ProgressReporter(Protocol):
    def add_task(self, description: str, total: float) -> Any:
        ...

    def update_task(self, task_id: Any, advance: float) -> None:
        ...

    def remove_task(self, task_id: Any) -> None:
        ...

class RichProgressReporter:
    def __init__(self, prog: Progress):
        self.prog = prog

    def add_task(self, description: str, total: float) -> TaskID:
        return self.prog.add_task(description, total=total)

    def update_task(self, task_id: TaskID, advance: float) -> None:
        self.prog.update(task_id, advance=advance)

    def remove_task(self, task_id: TaskID) -> None:
        self.prog.remove_task(task_id)
