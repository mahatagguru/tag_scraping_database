"""
Paginator abstraction for handling numbered pagination and infinite scroll.
"""

class Paginator:
    def __init__(self, fetch_page_func):
        self.fetch_page_func = fetch_page_func

    def paginate(self, *args, **kwargs):
        """Yield successive pages using the provided fetch_page_func."""
        pass
