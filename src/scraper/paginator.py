"""
Paginator abstraction for handling numbered pagination and infinite scroll.
"""
from typing import Any, Callable, Generator, Iterator


class Paginator:
    def __init__(self, fetch_page_func: Callable[..., Any]) -> None:
        self.fetch_page_func = fetch_page_func

    def paginate(self, *args: Any, **kwargs: Any) -> Generator[Any, None, None]:
        """Yield successive pages using the provided fetch_page_func."""
        yield from []
