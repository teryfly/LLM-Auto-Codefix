import time
import sys
from typing import Callable, Any

def exponential_backoff(base: int, factor: int, max_time: int, attempt: int) -> int:
    """Calculate exponential backoff time."""
    wait_time = min(base * (factor ** attempt), max_time)
    return wait_time

def prompt_user(question: str) -> bool:
    """Prompt the user for a yes/no confirmation in the console."""
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        elif answer in {"n", "no"}:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def retry_with_backoff(
    func: Callable[[], Any],
    max_attempts: int,
    base_wait: int,
    max_wait: int,
    factor: int = 2,
    on_fail: Callable[[Exception, int], None] = None
) -> Any:
    """Retry a function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if on_fail:
                on_fail(e, attempt)
            if attempt == max_attempts - 1:
                raise
            wait_time = exponential_backoff(base_wait, factor, max_wait, attempt)
            print(f"[Retry] Attempt {attempt+1}/{max_attempts} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

def exit_with_error(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)