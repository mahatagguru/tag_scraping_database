#!/usr/bin/env python3
"""
Multi-Runner Orchestration Script for TAG Grading Scraper
Coordinates multiple pipeline runners for high-throughput scraping with:
- Load balancing across multiple runners
- Automatic runner health monitoring
- Failover and recovery
- Centralized coordination and reporting
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import signal
import psutil

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import SessionLocal
from src.models import AuditLog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('multi_runner.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RunnerConfig:
    """Configuration for a single runner"""
    runner_id: str
    concurrency: int = 3
    delay: float = 1.0
    max_retries: int = 3
    retry_backoff: float = 2.0
    log_level: str = "INFO"
    working_directory: str = "."
    python_path: str = "python"

@dataclass
class RunnerStatus:
    """Status information for a runner"""
    runner_id: str
    pid: Optional[int] = None
    start_time: Optional[float] = None
    last_heartbeat: Optional[float] = None
    status: str = "stopped"  # stopped, starting, running, failed, completed
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    results: Optional[Dict] = None

class MultiRunnerOrchestrator:
    """Orchestrates multiple pipeline runners"""
    
    def __init__(self, base_config: RunnerConfig, num_runners: int = 3):
        self.base_config = base_config
        self.num_runners = num_runners
        self.runners: Dict[str, RunnerStatus] = {}
        self.coordination_lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Multi-runner orchestrator initialized with {num_runners} runners")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown_event.set()
    
    def create_runner_configs(self) -> List[RunnerConfig]:
        """Create configurations for all runners"""
        configs = []
        
        for i in range(self.num_runners):
            config = RunnerConfig(
                runner_id=f"{self.base_config.runner_id}_runner_{i+1}",
                concurrency=self.base_config.concurrency,
                delay=self.base_config.delay,
                max_retries=self.base_config.max_retries,
                retry_backoff=self.base_config.retry_backoff,
                log_level=self.base_config.log_level,
                working_directory=self.base_config.working_directory,
                python_path=self.base_config.python_path
            )
            configs.append(config)
        
        return configs
    
    def start_runner(self, config: RunnerConfig) -> RunnerStatus:
        """Start a single pipeline runner"""
        logger.info(f"🚀 Starting runner: {config.runner_id}")
        
        # Create runner status
        runner_status = RunnerStatus(
            runner_id=config.runner_id,
            start_time=time.time(),
            status="starting"
        )
        
        try:
            # Build command
            cmd = [
                config.python_path,
                "src/scraper/unified_pipeline.py",
                "--runner-id", config.runner_id,
                "--concurrency", str(config.concurrency),
                "--delay", str(config.delay),
                "--max-retries", str(config.max_retries),
                "--retry-backoff", str(config.retry_backoff),
                "--log-level", config.log_level
            ]
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=config.working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update status
            runner_status.pid = process.pid
            runner_status.status = "running"
            runner_status.last_heartbeat = time.time()
            
            logger.info(f"✅ Runner {config.runner_id} started with PID {process.pid}")
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_runner,
                args=(config.runner_id, process),
                daemon=True
            )
            monitor_thread.start()
            
            return runner_status
            
        except Exception as e:
            logger.error(f"❌ Failed to start runner {config.runner_id}: {e}")
            runner_status.status = "failed"
            runner_status.error_message = str(e)
            return runner_status
    
    def _monitor_runner(self, runner_id: str, process: subprocess.Popen):
        """Monitor a running pipeline process"""
        try:
            # Wait for process to complete
            stdout, stderr = process.communicate()
            exit_code = process.returncode
            
            with self.coordination_lock:
                if runner_id in self.runners:
                    runner = self.runners[runner_id]
                    runner.status = "completed" if exit_code == 0 else "failed"
                    runner.exit_code = exit_code
                    runner.last_heartbeat = time.time()
                    
                    if exit_code == 0:
                        logger.info(f"✅ Runner {runner_id} completed successfully")
                        # Try to parse results from stdout
                        try:
                            # Look for JSON results in output
                            for line in stdout.split('\n'):
                                if line.strip().startswith('{') and line.strip().endswith('}'):
                                    runner.results = json.loads(line.strip())
                                    break
                        except:
                            pass
                    else:
                        logger.error(f"❌ Runner {runner_id} failed with exit code {exit_code}")
                        if stderr:
                            runner.error_message = stderr.strip()
                            logger.error(f"   Error: {stderr.strip()}")
                else:
                    logger.warning(f"Runner {runner_id} not found in status tracking")
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring runner {runner_id}: {e}")
            with self.coordination_lock:
                if runner_id in self.runners:
                    self.runners[runner_id].status = "failed"
                    self.runners[runner_id].error_message = str(e)
    
    def start_all_runners(self):
        """Start all pipeline runners"""
        logger.info(f"🚀 Starting {self.num_runners} pipeline runners...")
        
        # Create runner configurations
        runner_configs = self.create_runner_configs()
        
        # Start all runners
        for config in runner_configs:
            runner_status = self.start_runner(config)
            self.runners[config.runner_id] = runner_status
            
            # Small delay between starts to avoid overwhelming the system
            time.sleep(1)
        
        logger.info(f"✅ All {self.num_runners} runners started")
    
    def monitor_runners(self, check_interval: float = 10.0):
        """Monitor all runners and report status"""
        logger.info(f"📊 Starting runner monitoring (check interval: {check_interval}s)")
        
        while not self.shutdown_event.is_set():
            try:
                self._print_runner_status()
                
                # Check for completed runners
                completed_count = sum(1 for r in self.runners.values() if r.status == "completed")
                failed_count = sum(1 for r in self.runners.values() if r.status == "failed")
                
                if completed_count + failed_count == len(self.runners):
                    logger.info("🏁 All runners have completed")
                    break
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
    
    def _print_runner_status(self):
        """Print current status of all runners"""
        logger.info("=" * 80)
        logger.info("RUNNER STATUS REPORT")
        logger.info("=" * 80)
        
        for runner_id, status in self.runners.items():
            uptime = ""
            if status.start_time and status.last_heartbeat:
                uptime = f" (uptime: {status.last_heartbeat - status.start_time:.1f}s)"
            
            logger.info(f"Runner: {runner_id}")
            logger.info(f"  Status: {status.status}")
            logger.info(f"  PID: {status.pid or 'N/A'}")
            logger.info(f"  Uptime: {uptime}")
            
            if status.exit_code is not None:
                logger.info(f"  Exit Code: {status.exit_code}")
            
            if status.error_message:
                logger.info(f"  Error: {status.error_message}")
            
            if status.results:
                logger.info(f"  Results: {status.results}")
            
            logger.info("")
    
    def stop_all_runners(self):
        """Stop all running pipeline runners"""
        logger.info("🛑 Stopping all runners...")
        
        for runner_id, status in self.runners.items():
            if status.pid and status.status == "running":
                try:
                    logger.info(f"Stopping runner {runner_id} (PID: {status.pid})")
                    
                    # Try graceful shutdown first
                    process = psutil.Process(status.pid)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ Runner {runner_id} stopped gracefully")
                    except psutil.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        logger.warning(f"Force killing runner {runner_id}")
                        process.kill()
                        process.wait()
                        logger.info(f"✅ Runner {runner_id} force stopped")
                        
                except psutil.NoSuchProcess:
                    logger.info(f"Runner {runner_id} process already terminated")
                except Exception as e:
                    logger.error(f"Error stopping runner {runner_id}: {e}")
        
        logger.info("✅ All runners stopped")
    
    def get_final_summary(self) -> Dict[str, Any]:
        """Get final summary of all runner results"""
        logger.info("📊 Compiling final results summary...")
        
        summary = {
            'total_runners': len(self.runners),
            'completed_runners': 0,
            'failed_runners': 0,
            'total_categories': 0,
            'total_years': 0,
            'total_sets': 0,
            'total_cards': 0,
            'total_grade_rows': 0,
            'total_pages': 0,
            'total_errors': 0,
            'total_duration': 0,
            'runner_results': []
        }
        
        for runner_id, status in self.runners.items():
            runner_summary = {
                'runner_id': runner_id,
                'status': status.status,
                'exit_code': status.exit_code,
                'error_message': status.error_message,
                'results': status.results
            }
            
            if status.status == "completed":
                summary['completed_runners'] += 1
                if status.results:
                    summary['total_categories'] += status.results.get('categories_processed', 0)
                    summary['total_years'] += status.results.get('total_years', 0)
                    summary['total_sets'] += status.results.get('total_sets', 0)
                    summary['total_cards'] += status.results.get('total_cards', 0)
                    summary['total_grade_rows'] += status.results.get('total_grade_rows', 0)
                    summary['total_pages'] += status.results.get('pages_scraped', 0)
                    summary['total_errors'] += status.results.get('error_count', 0)
                    summary['total_duration'] += status.results.get('duration_seconds', 0)
            elif status.status == "failed":
                summary['failed_runners'] += 1
            
            summary['runner_results'].append(runner_summary)
        
        return summary
    
    def run_orchestration(self, check_interval: float = 10.0):
        """Run the complete multi-runner orchestration"""
        try:
            # Start all runners
            self.start_all_runners()
            
            # Monitor runners
            self.monitor_runners(check_interval)
            
            # Get final summary
            final_summary = self.get_final_summary()
            
            # Print final summary
            self._print_final_summary(final_summary)
            
            return final_summary
            
        except KeyboardInterrupt:
            logger.info("Orchestration interrupted by user")
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
        finally:
            # Always stop runners on exit
            self.stop_all_runners()
    
    def _print_final_summary(self, summary: Dict[str, Any]):
        """Print final orchestration summary"""
        logger.info("=" * 80)
        logger.info("MULTI-RUNNER ORCHESTRATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Runners: {summary['total_runners']}")
        logger.info(f"Completed: {summary['completed_runners']}")
        logger.info(f"Failed: {summary['failed_runners']}")
        logger.info("")
        logger.info("AGGREGATED RESULTS:")
        logger.info(f"  Categories: {summary['total_categories']}")
        logger.info(f"  Years: {summary['total_years']}")
        logger.info(f"  Sets: {summary['total_sets']}")
        logger.info(f"  Cards: {summary['total_cards']}")
        logger.info(f"  Grade Rows: {summary['total_grade_rows']}")
        logger.info(f"  Pages Scraped: {summary['total_pages']}")
        logger.info(f"  Total Errors: {summary['total_errors']}")
        logger.info(f"  Total Duration: {summary['total_duration']:.1f}s")
        logger.info("=" * 80)

def main():
    """Main entry point for multi-runner orchestration"""
    parser = argparse.ArgumentParser(
        description='Multi-Runner TAG Grading Scraper Orchestrator'
    )
    
    # Orchestration configuration
    parser.add_argument('--num-runners', type=int, default=3,
                       help='Number of concurrent pipeline runners (default: 3)')
    parser.add_argument('--check-interval', type=float, default=10.0,
                       help='Status check interval in seconds (default: 10.0)')
    
    # Runner configuration
    parser.add_argument('--concurrency', type=int, default=3,
                       help='Concurrency per runner (default: 3)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests per runner (default: 1.0)')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Max retries per runner (default: 3)')
    parser.add_argument('--retry-backoff', type=float, default=2.0,
                       help='Retry backoff per runner (default: 2.0)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Log level per runner (default: INFO)')
    
    # System configuration
    parser.add_argument('--working-directory', default='.',
                       help='Working directory for runners (default: current)')
    parser.add_argument('--python-path', default='python',
                       help='Python executable path (default: python)')
    
    args = parser.parse_args()
    
    # Create base configuration
    base_config = RunnerConfig(
        runner_id=f"orchestrator_{int(time.time())}",
        concurrency=args.concurrency,
        delay=args.delay,
        max_retries=args.max_retries,
        retry_backoff=args.retry_backoff,
        log_level=args.log_level,
        working_directory=args.working_directory,
        python_path=args.python_path
    )
    
    # Create and run orchestrator
    orchestrator = MultiRunnerOrchestrator(base_config, args.num_runners)
    
    try:
        results = orchestrator.run_orchestration(args.check_interval)
        
        if results['failed_runners'] == 0:
            logger.info("🎉 All runners completed successfully!")
            return 0
        else:
            logger.warning(f"⚠️  {results['failed_runners']} runners failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Orchestration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
