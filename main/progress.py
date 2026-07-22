from typing import Protocol, Any, Optional
from rich.progress import Progress, TaskID

class ProgressReporter(Protocol):
    def add_task(self, description: str, total: float) -> Any:
        ...

    def update_task(self, task_id: Any, advance: float = 0.0, completed: Optional[float] = None) -> None:
        ...

    def remove_task(self, task_id: Any) -> None:
        ...

class RichProgressReporter:
    def __init__(self, prog: Progress):
        self.prog = prog

    def add_task(self, description: str, total: float) -> TaskID:
        return self.prog.add_task(description, total=total)

    def update_task(self, task_id: TaskID, advance: float = 0.0, completed: Optional[float] = None) -> None:
        kwargs = {}
        if advance > 0:
            kwargs['advance'] = advance
        if completed is not None:
            kwargs['completed'] = completed
        self.prog.update(task_id, **kwargs)

    def remove_task(self, task_id: TaskID) -> None:
        self.prog.remove_task(task_id)
