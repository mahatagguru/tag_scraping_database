#!/usr/bin/env python3
"""Python version compatibility shims."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    try:
        from exceptiongroup import ExceptionGroup
    except ImportError:
        # Fallback: create a simple ExceptionGroup-like class
        class ExceptionGroup(Exception):  # type: ignore[no-redef]
            def __init__(self, message: str, exceptions: list[Exception]):
                super().__init__(message)
                self.exceptions = exceptions

    # Provide a BaseExceptionGroup-compatible name for older runtimes
    BaseExceptionGroup = ExceptionGroup
else:
    from builtins import BaseExceptionGroup

    ExceptionGroup = BaseExceptionGroup  # type: ignore[no-redef,misc]

__all__ = ["ExceptionGroup", "BaseExceptionGroup"]
