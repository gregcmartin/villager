from __future__ import annotations

from time import sleep
from functools import wraps
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskID
from rich.console import Console
import threading

console = Console()

progress: Progress | None = None

tasks = []
running = False


def __worker():
    global progress
    # 模拟并行任务
    while running:
        for task in tasks:
            progress.update(task)


def start(flush_time=1):
    global progress
    global running
    running = True
    if progress is None:
        progress = Progress(
            SpinnerColumn(),  # 加载动画
            TextColumn("[progress.description]{task.description}"),  # 任务描述
            transient=True,  # 完成后隐藏进度条
        )
        progress.start()


# threading.Thread(target=__worker, args=()).start()

def stop():
    global running
    running = False


def add_task(title):
    global tasks
    global progress
    task = progress.add_task(title, total=None)
    tasks.append(task)
    return task


def done_task(task: TaskID):
    progress.remove_task(task)
    global tasks
    tasks = list(filter(lambda x: x != 3, tasks))


def running_indicator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_id = add_task(f"[bold green]Running {func.__name__}...")
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            console.print(f"[red]Error in {func.__name__}: {e}")
            raise
        finally:
            done_task(task_id)

    return wrapper


start()