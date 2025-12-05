#!/usr/bin/env python3
"""
Monitoring and profiling system for the scraping pipeline.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import time
from typing import Any

import aiofiles
import psutil
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class PerformanceMetrics:
    """Performance metrics collector."""

    def __init__(self, max_history: int = 1000):
        """Initialize performance metrics."""
        self.max_history = max_history

        # Metrics storage
        self._metrics_history: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._current_metrics: dict[str, Any] = {}

        # Prometheus metrics
        self._registry = CollectorRegistry()

        # HTTP metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests made",
            ["method", "status_code", "endpoint"],
            registry=self._registry,
        )

        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            registry=self._registry,
        )

        # Database metrics
        self.db_operations_total = Counter(
            "db_operations_total",
            "Total database operations",
            ["operation_type", "table"],
            registry=self._registry,
        )

        self.db_operation_duration = Histogram(
            "db_operation_duration_seconds",
            "Database operation duration in seconds",
            ["operation_type", "table"],
            registry=self._registry,
        )

        # Scraping metrics
        self.items_scraped_total = Counter(
            "items_scraped_total",
            "Total items scraped",
            ["item_type", "status"],
            registry=self._registry,
        )

        self.scraping_errors_total = Counter(
            "scraping_errors_total",
            "Total scraping errors",
            ["error_type", "component"],
            registry=self._registry,
        )

        # System metrics
        self.cpu_usage = Gauge(
            "cpu_usage_percent", "CPU usage percentage", registry=self._registry
        )

        self.memory_usage = Gauge(
            "memory_usage_bytes", "Memory usage in bytes", registry=self._registry
        )

        self.active_connections = Gauge(
            "active_connections",
            "Number of active connections",
            registry=self._registry,
        )

        # Start background monitoring
        self._monitoring_task = None
        self._start_monitoring()

    def _start_monitoring(self) -> None:
        """Start background monitoring task."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(
                self._monitor_system_resources()
            )

    async def _monitor_system_resources(self) -> None:
        """Monitor system resources in background."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)
                self._record_metric("cpu_usage_percent", cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.used)
                self._record_metric("memory_usage_bytes", memory.used)
                self._record_metric("memory_usage_percent", memory.percent)

                # Network connections
                connections = len(psutil.net_connections())
                self.active_connections.set(connections)
                self._record_metric("active_connections", connections)

                # Disk usage
                disk = psutil.disk_usage("/")
                self._record_metric(
                    "disk_usage_percent", (disk.used / disk.total) * 100
                )

                await asyncio.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                print(f"Error in system monitoring: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    def _record_metric(self, name: str, value: Any) -> None:
        """Record a metric value."""
        timestamp = time.time()
        self._metrics_history[name].append((timestamp, value))
        self._current_metrics[name] = value

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, status_code=str(status_code), endpoint=endpoint
        ).inc()

        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        self._record_metric("http_request_duration", duration)

    def record_db_operation(
        self, operation_type: str, table: str, duration: float
    ) -> None:
        """Record database operation metrics."""
        self.db_operations_total.labels(
            operation_type=operation_type, table=table
        ).inc()

        self.db_operation_duration.labels(
            operation_type=operation_type, table=table
        ).observe(duration)

        self._record_metric("db_operation_duration", duration)

    def record_scraped_item(self, item_type: str, status: str = "success") -> None:
        """Record scraped item metrics."""
        self.items_scraped_total.labels(item_type=item_type, status=status).inc()

        self._record_metric(f"items_scraped_{item_type}", 1)

    def record_scraping_error(self, error_type: str, component: str) -> None:
        """Record scraping error metrics."""
        self.scraping_errors_total.labels(
            error_type=error_type, component=component
        ).inc()

        self._record_metric("scraping_errors", 1)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        summary = {
            "current_metrics": self._current_metrics.copy(),
            "prometheus_metrics": generate_latest(self._registry).decode("utf-8"),
        }

        # Calculate averages for recent metrics
        now = time.time()
        recent_window = 300  # 5 minutes

        for metric_name, history in self._metrics_history.items():
            recent_values = [
                value for timestamp, value in history if now - timestamp < recent_window
            ]

            if recent_values:
                summary[f"{metric_name}_recent_avg"] = sum(recent_values) / len(
                    recent_values
                )
                summary[f"{metric_name}_recent_max"] = max(recent_values)
                summary[f"{metric_name}_recent_min"] = min(recent_values)

        return summary

    async def save_metrics_to_file(self, filepath: str) -> None:
        """Save metrics to file."""
        summary = self.get_metrics_summary()
        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(summary, indent=2, default=str))

    async def cleanup(self) -> None:
        """Cleanup monitoring resources."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass


class Profiler:
    """Code profiler for identifying bottlenecks."""

    def __init__(self, enabled: bool = True):
        """Initialize profiler."""
        self.enabled = enabled
        self._profiles: dict[str, list[tuple[float, float]]] = defaultdict(
            list
        )  # name -> [(start_time, duration)]
        self._active_profiles: dict[str, float] = {}  # name -> start_time

    def start_profile(self, name: str) -> None:
        """Start profiling a code section."""
        if not self.enabled:
            return

        self._active_profiles[name] = time.perf_counter()

    def end_profile(self, name: str) -> float:
        """End profiling a code section and return duration."""
        if not self.enabled or name not in self._active_profiles:
            return 0.0

        start_time = self._active_profiles.pop(name)
        duration = time.perf_counter() - start_time

        self._profiles[name].append((start_time, duration))

        return duration

    async def __aenter__(self, name: str):
        """Async context manager for profiling."""
        self.start_profile(name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb, name: str):
        """Async context manager exit."""
        self.end_profile(name)

    def get_profile_summary(self) -> dict[str, dict[str, Any]]:
        """Get profiling summary."""
        summary = {}

        for name, profile_data in self._profiles.items():
            if not profile_data:
                continue

            durations = [duration for _, duration in profile_data]
            total_time = sum(durations)
            avg_time = total_time / len(durations)

            summary[name] = {
                "total_calls": len(durations),
                "total_time": total_time,
                "average_time": avg_time,
                "min_time": min(durations),
                "max_time": max(durations),
                "total_percentage": 0,  # Will be calculated relative to total
            }

        # Calculate percentages
        total_all_time = sum(data["total_time"] for data in summary.values())
        if total_all_time > 0:
            for data in summary.values():
                data["total_percentage"] = (data["total_time"] / total_all_time) * 100

        return summary

    def get_bottlenecks(
        self, threshold_percentage: float = 10.0
    ) -> list[tuple[str, dict[str, Any]]]:
        """Get code bottlenecks above threshold percentage."""
        summary = self.get_profile_summary()
        bottlenecks = []

        for name, data in summary.items():
            if data["total_percentage"] >= threshold_percentage:
                bottlenecks.append((name, data))

        return sorted(bottlenecks, key=lambda x: x[1]["total_percentage"], reverse=True)


class MonitoringManager:
    """Central monitoring manager."""

    def __init__(self, metrics_file: str = "scraping_metrics.json"):
        """Initialize monitoring manager."""
        self.metrics_file = metrics_file
        self.metrics = PerformanceMetrics()
        self.profiler = Profiler()
        self._start_time = time.time()

    def get_runtime_stats(self) -> dict[str, Any]:
        """Get runtime statistics."""
        runtime = time.time() - self._start_time

        return {
            "runtime_seconds": runtime,
            "runtime_formatted": str(timedelta(seconds=int(runtime))),
            "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
            "current_time": datetime.now().isoformat(),
        }

    async def save_report(self, filepath: str | None = None) -> None:
        """Save monitoring report."""
        filepath = filepath or self.metrics_file

        report = {
            "runtime_stats": self.get_runtime_stats(),
            "performance_metrics": self.metrics.get_metrics_summary(),
            "profiling_summary": self.profiler.get_profile_summary(),
            "bottlenecks": self.profiler.get_bottlenecks(),
        }

        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(report, indent=2, default=str))

    async def cleanup(self) -> None:
        """Cleanup monitoring resources."""
        await self.metrics.cleanup()
        await self.save_report()


# Global monitoring instance
_monitoring_manager: MonitoringManager | None = None


def get_monitoring_manager() -> MonitoringManager:
    """Get global monitoring manager instance."""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager


# Decorators for easy profiling
def profile_function(name: str | None = None):
    """Decorator to profile a function."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            monitor = get_monitoring_manager()
            profile_name = name or f"{func.__module__}.{func.__name__}"

            monitor.profiler.start_profile(profile_name)
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            finally:
                monitor.profiler.end_profile(profile_name)

        def sync_wrapper(*args, **kwargs):
            monitor = get_monitoring_manager()
            profile_name = name or f"{func.__module__}.{func.__name__}"

            monitor.profiler.start_profile(profile_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.profiler.end_profile(profile_name)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
