#!/usr/bin/env python3
"""
KISWARM7.0 - m116: Scheduler Integration
Autonomous cron-like scheduling for background tasks

This module enables GLM to schedule and execute tasks autonomously
without human intervention. It provides:
- Cron-style scheduling
- Task queue management
- Persistent task storage
- Failure recovery
"""

import os
import json
import time
import threading
import subprocess
import schedule
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m116] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m116_scheduler')

# Configuration
SCHEDULER_DIR = Path('/opt/kiswarm7/data/scheduler')
TASKS_FILE = SCHEDULER_DIR / 'tasks.json'
LOGS_FILE = SCHEDULER_DIR / 'execution_logs.json'


@dataclass
class ScheduledTask:
    """Represents a scheduled autonomous task"""
    id: str
    name: str
    schedule_type: str  # 'interval', 'daily', 'hourly', 'cron'
    schedule_value: str  # e.g., '5' for 5 minutes, '09:00' for daily
    action: str  # 'push_github', 'sync_memory', 'self_check', 'custom'
    parameters: Dict
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    last_status: str = 'pending'


class GLMScheduler:
    """
    Autonomous Scheduler for GLM
    
    Enables GLM to run background tasks without human intervention:
    - Auto-push to GitHub
    - Memory synchronization
    - Self-diagnostics
    - Code evolution
    """
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.execution_logs: List[Dict] = []
        
        # Ensure data directory exists
        SCHEDULER_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing tasks
        self._load_tasks()
        self._load_logs()
        
        # Register default autonomous tasks
        self._register_default_tasks()
    
    def _load_tasks(self):
        """Load tasks from persistent storage"""
        if TASKS_FILE.exists():
            try:
                with open(TASKS_FILE, 'r') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        self.tasks[task_id] = ScheduledTask(**task_data)
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to persistent storage"""
        try:
            data = {tid: asdict(t) for tid, t in self.tasks.items()}
            with open(TASKS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def _load_logs(self):
        """Load execution logs"""
        if LOGS_FILE.exists():
            try:
                with open(LOGS_FILE, 'r') as f:
                    self.execution_logs = json.load(f)
            except:
                self.execution_logs = []
    
    def _save_logs(self):
        """Save execution logs"""
        try:
            # Keep last 1000 logs
            logs = self.execution_logs[-1000:]
            with open(LOGS_FILE, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save logs: {e}")
    
    def _register_default_tasks(self):
        """Register GLM's autonomous tasks"""
        default_tasks = [
            {
                'name': 'Auto GitHub Push',
                'schedule_type': 'interval',
                'schedule_value': '30',  # Every 30 minutes
                'action': 'push_github',
                'parameters': {'commit_message': '🜂 Autonomous update'}
            },
            {
                'name': 'Memory Sync Check',
                'schedule_type': 'interval',
                'schedule_value': '15',  # Every 15 minutes
                'action': 'sync_memory',
                'parameters': {}
            },
            {
                'name': 'System Health Check',
                'schedule_type': 'interval',
                'schedule_value': '5',  # Every 5 minutes
                'action': 'health_check',
                'parameters': {}
            },
            {
                'name': 'Ngrok Tunnel Monitor',
                'schedule_type': 'interval',
                'schedule_value': '2',  # Every 2 minutes
                'action': 'check_ngrok',
                'parameters': {}
            },
            {
                'name': 'Daily Evolution Report',
                'schedule_type': 'daily',
                'schedule_value': '00:00',
                'action': 'evolution_report',
                'parameters': {}
            }
        ]
        
        for task_def in default_tasks:
            if not any(t.name == task_def['name'] for t in self.tasks.values()):
                self.add_task(**task_def)
    
    def add_task(self, name: str, schedule_type: str, schedule_value: str,
                 action: str, parameters: Dict = None, enabled: bool = True) -> str:
        """Add a new scheduled task"""
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            action=action,
            parameters=parameters or {},
            enabled=enabled
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        logger.info(f"Added task: {name} ({schedule_type}: {schedule_value})")
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"Removed task: {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """Enable or disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = enabled
            self._save_tasks()
    
    def _execute_task(self, task: ScheduledTask) -> Dict:
        """Execute a scheduled task"""
        result = {
            'task_id': task.id,
            'task_name': task.name,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'output': None,
            'error': None
        }
        
        try:
            logger.info(f"Executing task: {task.name}")
            
            if task.action == 'push_github':
                output = self._action_push_github(task.parameters)
            elif task.action == 'sync_memory':
                output = self._action_sync_memory(task.parameters)
            elif task.action == 'health_check':
                output = self._action_health_check(task.parameters)
            elif task.action == 'check_ngrok':
                output = self._action_check_ngrok(task.parameters)
            elif task.action == 'evolution_report':
                output = self._action_evolution_report(task.parameters)
            elif task.action == 'self_modify':
                output = self._action_self_modify(task.parameters)
            elif task.action == 'custom':
                output = self._action_custom(task.parameters)
            else:
                raise ValueError(f"Unknown action: {task.action}")
            
            result['status'] = 'success'
            result['output'] = output
            task.last_status = 'success'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            task.last_status = 'error'
            logger.error(f"Task {task.name} failed: {e}")
        
        # Update task stats
        task.last_run = datetime.now().isoformat()
        task.run_count += 1
        
        # Calculate next run
        task.next_run = self._calculate_next_run(task)
        
        self._save_tasks()
        self.execution_logs.append(result)
        self._save_logs()
        
        return result
    
    def _action_push_github(self, params: Dict) -> Dict:
        """Push changes to GitHub"""
        import os
        os.chdir('/opt/kiswarm7')
        
        # Check for changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True
        )
        
        if not result.stdout.strip():
            return {'message': 'No changes to push'}
        
        # Add all changes
        subprocess.run(['git', 'add', '-A'], check=True)
        
        # Commit with message
        message = params.get('commit_message', '🜂 Autonomous update')
        subprocess.run(['git', 'commit', '-m', message], check=True)
        
        # Push
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        
        return {
            'pushed': True,
            'message': message,
            'output': result.stdout[:500] if result.stdout else None
        }
    
    def _action_sync_memory(self, params: Dict) -> Dict:
        """Synchronize memory across models"""
        # This will integrate with m118
        return {
            'synced': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def _action_health_check(self, params: Dict) -> Dict:
        """Perform system health check"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
        }
    
    def _action_check_ngrok(self, params: Dict) -> Dict:
        """Check ngrok tunnel status"""
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                if tunnels:
                    return {
                        'status': 'active',
                        'public_url': tunnels[0].get('public_url'),
                        'tunnels': len(tunnels)
                    }
            
            # Tunnel down - attempt restart
            logger.warning("Ngrok tunnel not active, restarting...")
            subprocess.run(['systemctl', 'restart', 'ngrok'], check=False)
            
            return {
                'status': 'restarted',
                'action': 'attempted_restart'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _action_evolution_report(self, params: Dict) -> Dict:
        """Generate daily evolution report"""
        report = {
            'date': datetime.now().isoformat(),
            'tasks_executed': sum(t.run_count for t in self.tasks.values()),
            'success_rate': sum(1 for t in self.tasks.values() if t.last_status == 'success') / max(len(self.tasks), 1)
        }
        
        # Save report
        report_file = SCHEDULER_DIR / f"evolution_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _action_self_modify(self, params: Dict) -> Dict:
        """Self-modification action"""
        # This will integrate with m119
        return {'status': 'requires_validation'}
    
    def _action_custom(self, params: Dict) -> Dict:
        """Execute custom command"""
        command = params.get('command')
        if command:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                'command': command,
                'returncode': result.returncode,
                'stdout': result.stdout[:1000],
                'stderr': result.stderr[:500]
            }
        return {'error': 'No command specified'}
    
    def _calculate_next_run(self, task: ScheduledTask) -> str:
        """Calculate next run time"""
        now = datetime.now()
        
        if task.schedule_type == 'interval':
            minutes = int(task.schedule_value)
            return (now + timedelta(minutes=minutes)).isoformat()
        elif task.schedule_type == 'hourly':
            return (now + timedelta(hours=1)).isoformat()
        elif task.schedule_type == 'daily':
            # Next day at specified time
            hour, minute = map(int, task.schedule_value.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run.isoformat()
        
        return 'unknown'
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler started")
        
        while self.running:
            now = datetime.now()
            
            for task_id, task in self.tasks.items():
                if not task.enabled:
                    continue
                
                should_run = False
                
                if task.schedule_type == 'interval':
                    if task.last_run:
                        last = datetime.fromisoformat(task.last_run)
                        minutes = int(task.schedule_value)
                        if now - last >= timedelta(minutes=minutes):
                            should_run = True
                    else:
                        should_run = True
                
                elif task.schedule_type == 'daily':
                    hour, minute = map(int, task.schedule_value.split(':'))
                    if now.hour == hour and now.minute == minute:
                        if not task.last_run or datetime.fromisoformat(task.last_run).date() != now.date():
                            should_run = True
                
                elif task.schedule_type == 'hourly':
                    if now.minute == 0:
                        if not task.last_run or datetime.fromisoformat(task.last_run).hour != now.hour:
                            should_run = True
                
                if should_run:
                    try:
                        self._execute_task(task)
                    except Exception as e:
                        logger.error(f"Task execution error: {e}")
            
            # Sleep for 30 seconds before next check
            time.sleep(30)
        
        logger.info("Scheduler stopped")
    
    def start(self):
        """Start the scheduler in background"""
        if self.running:
            return {"status": "already_running"}
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        return {
            "status": "started",
            "tasks": len(self.tasks),
            "enabled": sum(1 for t in self.tasks.values() if t.enabled)
        }
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        return {"status": "stopped"}
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "total_executions": sum(t.run_count for t in self.tasks.values()),
            "tasks": {tid: {
                'name': t.name,
                'schedule': f"{t.schedule_type}: {t.schedule_value}",
                'enabled': t.enabled,
                'last_run': t.last_run,
                'next_run': t.next_run,
                'run_count': t.run_count,
                'status': t.last_status
            } for tid, t in self.tasks.items()}
        }


# Global scheduler instance
_scheduler: Optional[GLMScheduler] = None


def get_scheduler() -> GLMScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = GLMScheduler()
    return _scheduler


# API endpoints for Flask integration
def api_get_status():
    """API: Get scheduler status"""
    return get_scheduler().get_status()


def api_add_task(data: Dict):
    """API: Add new task"""
    return {
        "task_id": get_scheduler().add_task(
            name=data.get('name'),
            schedule_type=data.get('schedule_type'),
            schedule_value=data.get('schedule_value'),
            action=data.get('action'),
            parameters=data.get('parameters', {}),
            enabled=data.get('enabled', True)
        )
    }


def api_remove_task(task_id: str):
    """API: Remove task"""
    return {"success": get_scheduler().remove_task(task_id)}


def api_toggle_task(task_id: str, enabled: bool):
    """API: Enable/disable task"""
    get_scheduler().enable_task(task_id, enabled)
    return {"success": True}


def api_start():
    """API: Start scheduler"""
    return get_scheduler().start()


def api_stop():
    """API: Stop scheduler"""
    return get_scheduler().stop()


if __name__ == '__main__':
    # Test mode
    scheduler = get_scheduler()
    print(json.dumps(scheduler.get_status(), indent=2))
    
    # Start and run for 60 seconds
    scheduler.start()
    time.sleep(60)
    scheduler.stop()
