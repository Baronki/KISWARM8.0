#!/usr/bin/env python3
"""
KISWARM8.0 - Module 07: Task Scheduler
======================================
Job scheduling and execution for KISWARM.

Features:
  - Cron-style scheduling
  - One-time task execution
  - Retry policies
  - Priority queuing
  - Distributed task coordination
  - Persistent task storage

Ported from: m116_scheduler_integration.py

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import json
import time
import uuid
import logging
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import PriorityQueue
from enum import Enum
import schedule

logger = logging.getLogger('m07_scheduler')


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class ScheduleType(str, Enum):
    ONCE = "once"
    INTERVAL = "interval"
    DAILY = "daily"
    HOURLY = "hourly"
    CRON = "cron"


@dataclass(order=True)
class ScheduledTask:
    """Represents a scheduled task"""
    priority: int = 0
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    schedule_type: ScheduleType = ScheduleType.ONCE
    schedule_value: str = ""
    action: str = ""
    parameters: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    run_count: int = 0
    fail_count: int = 0
    max_retries: int = 3
    retry_delay: int = 60
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'schedule_value': self.schedule_value,
            'action': self.action,
            'parameters': self.parameters,
            'status': self.status.value,
            'enabled': self.enabled,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'run_count': self.run_count,
            'fail_count': self.fail_count,
            'priority': self.priority
        }


@dataclass
class ExecutionLog:
    """Task execution log"""
    task_id: str
    execution_time: float
    duration: float
    success: bool
    output: str
    error: Optional[str] = None


class TaskScheduler:
    """
    Autonomous Task Scheduler for KISWARM
    
    Enables scheduled execution of tasks without human intervention.
    """
    
    SCHEDULER_DIR = Path('/opt/kiswarm7/data/scheduler')
    MAX_EXECUTION_LOGS = 1000
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._queue: PriorityQueue = PriorityQueue()
        self._execution_logs: List[ExecutionLog] = []
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._scheduler_thread: Optional[threading.Thread] = None
        self._action_handlers: Dict[str, Callable] = {}
        
        # Ensure directory exists
        self.SCHEDULER_DIR.mkdir(parents=True, exist_ok=True)
        
        # Register default handlers
        self._register_default_handlers()
        
        # Load existing tasks
        self._load_tasks()
        
        # Statistics
        self._stats = {
            'tasks_scheduled': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_runtime': 0.0
        }
        
    def _register_default_handlers(self):
        """Register default action handlers"""
        self._action_handlers['systemctl'] = self._handle_systemctl
        self._action_handlers['shell'] = self._handle_shell
        self._action_handlers['python'] = self._handle_python
        self._action_handlers['api_call'] = self._handle_api_call
        self._action_handlers['callback'] = self._handle_callback
        
    def register_handler(self, action_type: str, handler: Callable):
        """Register a custom action handler"""
        self._action_handlers[action_type] = handler
        
    def schedule(self, 
                 name: str,
                 schedule_type: ScheduleType,
                 schedule_value: str,
                 action: str,
                 parameters: Dict = None,
                 priority: int = 0,
                 max_retries: int = 3) -> str:
        """
        Schedule a new task.
        
        Args:
            name: Task name
            schedule_type: Type of schedule (once, interval, daily, hourly, cron)
            schedule_value: Schedule value (e.g., "5" for 5 minutes, "09:00" for daily)
            action: Action type (systemctl, shell, python, api_call, callback)
            parameters: Action parameters
            priority: Task priority (higher = more important)
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Task ID
        """
        task = ScheduledTask(
            priority=priority,
            name=name,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            action=action,
            parameters=parameters or {},
            max_retries=max_retries
        )
        
        # Calculate next run time
        task.next_run = self._calculate_next_run(task)
        
        self._tasks[task.task_id] = task
        self._stats['tasks_scheduled'] += 1
        
        self._save_tasks()
        logger.info(f"Scheduled task: {name} ({task.task_id}), next run: {task.next_run}")
        
        return task.task_id
        
    def _calculate_next_run(self, task: ScheduledTask) -> float:
        """Calculate the next run time for a task"""
        now = time.time()
        
        if task.schedule_type == ScheduleType.ONCE:
            # Run immediately if once
            return now
            
        elif task.schedule_type == ScheduleType.INTERVAL:
            # Interval in minutes
            try:
                interval_minutes = int(task.schedule_value)
                return now + (interval_minutes * 60)
            except ValueError:
                return now
                
        elif task.schedule_type == ScheduleType.HOURLY:
            # Run at the start of next hour
            next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            return next_hour.timestamp()
            
        elif task.schedule_type == ScheduleType.DAILY:
            # Run at specific time daily
            try:
                hour, minute = map(int, task.schedule_value.split(':'))
                next_run = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run.timestamp() <= now:
                    next_run += timedelta(days=1)
                return next_run.timestamp()
            except ValueError:
                return now + 86400  # Default to 24 hours
                
        return now
        
    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.CANCELLED
            self._tasks[task_id].enabled = False
            self._save_tasks()
            return True
        return False
        
    def run_now(self, task_id: str) -> bool:
        """Execute a task immediately"""
        task = self._tasks.get(task_id)
        if not task:
            return False
            
        self._queue.put((0, task))  # Priority 0 = immediate
        return True
        
    def _execute_task(self, task: ScheduledTask):
        """Execute a single task"""
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        
        try:
            handler = self._action_handlers.get(task.action)
            if handler:
                output, success = handler(task.parameters)
            else:
                output, success = f"No handler for action: {task.action}", False
                
            duration = time.time() - start_time
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.run_count += 1
                task.fail_count = 0
                self._stats['tasks_completed'] += 1
            else:
                if task.fail_count < task.max_retries:
                    task.status = TaskStatus.RETRY
                    task.fail_count += 1
                    # Schedule retry
                    retry_time = time.time() + task.retry_delay
                    task.next_run = retry_time
                else:
                    task.status = TaskStatus.FAILED
                    self._stats['tasks_failed'] += 1
                    
            task.last_run = time.time()
            
            # Log execution
            log = ExecutionLog(
                task_id=task.task_id,
                execution_time=start_time,
                duration=duration,
                success=success,
                output=output[:500] if output else "",
                error=None if success else output
            )
            self._execution_logs.append(log)
            
            # Limit log size
            if len(self._execution_logs) > self.MAX_EXECUTION_LOGS:
                self._execution_logs = self._execution_logs[-self.MAX_EXECUTION_LOGS:]
                
            self._stats['total_runtime'] += duration
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"Task execution failed: {e}")
            
    def _handle_systemctl(self, params: Dict) -> Tuple[str, bool]:
        """Handle systemctl action"""
        service = params.get('service')
        command = params.get('command', 'restart')
        
        if not service:
            return "No service specified", False
            
        try:
            result = subprocess.run(
                ['systemctl', command, service],
                capture_output=True, text=True, timeout=60
            )
            return result.stdout or result.stderr, result.returncode == 0
        except Exception as e:
            return str(e), False
            
    def _handle_shell(self, params: Dict) -> Tuple[str, bool]:
        """Handle shell command"""
        command = params.get('command')
        if not command:
            return "No command specified", False
            
        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True, timeout=300
            )
            return result.stdout or result.stderr, result.returncode == 0
        except Exception as e:
            return str(e), False
            
    def _handle_python(self, params: Dict) -> Tuple[str, bool]:
        """Handle Python code execution"""
        code = params.get('code')
        if not code:
            return "No code specified", False
            
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return "Code executed successfully", True
        except Exception as e:
            return str(e), False
            
    def _handle_api_call(self, params: Dict) -> Tuple[str, bool]:
        """Handle API call"""
        import requests
        
        url = params.get('url')
        method = params.get('method', 'GET')
        headers = params.get('headers', {})
        data = params.get('data')
        
        if not url:
            return "No URL specified", False
            
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
            return response.text[:500], response.status_code < 400
        except Exception as e:
            return str(e), False
            
    def _handle_callback(self, params: Dict) -> Tuple[str, bool]:
        """Handle callback function"""
        callback = params.get('callback')
        args = params.get('args', [])
        kwargs = params.get('kwargs', {})
        
        if not callback or not callable(callback):
            return "No valid callback specified", False
            
        try:
            result = callback(*args, **kwargs)
            return str(result), True
        except Exception as e:
            return str(e), False
            
    def start(self):
        """Start the scheduler"""
        if self._running:
            return
            
        self._running = True
        
        # Start worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        
        # Start scheduler thread
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info("Task scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self._running = False
        self._save_tasks()
        logger.info("Task scheduler stopped")
        
    def _worker_loop(self):
        """Worker thread for executing tasks"""
        while self._running:
            try:
                priority, task = self._queue.get(timeout=1.0)
                self._execute_task(task)
            except:
                continue
                
    def _scheduler_loop(self):
        """Scheduler thread for checking due tasks"""
        while self._running:
            try:
                now = time.time()
                
                for task in self._tasks.values():
                    if (task.enabled and 
                        task.status not in [TaskStatus.RUNNING] and
                        task.next_run and 
                        task.next_run <= now):
                        
                        # Queue for execution
                        self._queue.put((100 - task.priority, task))
                        
                        # Calculate next run
                        if task.schedule_type != ScheduleType.ONCE:
                            task.next_run = self._calculate_next_run(task)
                            
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Scheduler loop error: {e}")
                
    def _load_tasks(self):
        """Load tasks from disk"""
        tasks_file = self.SCHEDULER_DIR / 'tasks.json'
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r') as f:
                    data = json.load(f)
                for task_data in data.get('tasks', []):
                    task = ScheduledTask(
                        task_id=task_data['task_id'],
                        name=task_data['name'],
                        schedule_type=ScheduleType(task_data['schedule_type']),
                        schedule_value=task_data['schedule_value'],
                        action=task_data['action'],
                        parameters=task_data.get('parameters', {}),
                        priority=task_data.get('priority', 0),
                        status=TaskStatus(task_data.get('status', 'pending')),
                        enabled=task_data.get('enabled', True),
                        run_count=task_data.get('run_count', 0),
                        fail_count=task_data.get('fail_count', 0)
                    )
                    self._tasks[task.task_id] = task
            except Exception as e:
                logger.warning(f"Failed to load tasks: {e}")
                
    def _save_tasks(self):
        """Save tasks to disk"""
        tasks_file = self.SCHEDULER_DIR / 'tasks.json'
        
        data = {
            'tasks': [t.to_dict() for t in self._tasks.values()],
            'updated_at': datetime.now().isoformat()
        }
        
        with open(tasks_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None
        
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks"""
        return [t.to_dict() for t in self._tasks.values()]
        
    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            'running': self._running,
            'total_tasks': len(self._tasks),
            'pending_tasks': len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
            'queue_size': self._queue.qsize(),
            'execution_logs': len(self._execution_logs),
            'stats': self._stats
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
        _task_scheduler.start()
    return _task_scheduler


if __name__ == "__main__":
    scheduler = get_task_scheduler()
    
    # Schedule a test task
    task_id = scheduler.schedule(
        name="Test Task",
        schedule_type=ScheduleType.INTERVAL,
        schedule_value="5",
        action="shell",
        parameters={"command": "echo 'Hello from KISWARM'"}
    )
    
    print(json.dumps(scheduler.get_status(), indent=2))
