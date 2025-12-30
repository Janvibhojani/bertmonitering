# utils/memory_manager.py - NEW FILE (optional)
import gc
import asyncio
import logging
import psutil
import os
import threading
import time

class ResourceMonitor:
    """
    Monitor and manage system resources
    """
    def __init__(self, 
                 memory_limit_mb=2048, 
                 cpu_limit_percent=80,
                 check_interval=30):
        
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.cpu_limit = cpu_limit_percent
        self.check_interval = check_interval
        self.running = False
        self.process = psutil.Process(os.getpid())
        self.stats = {
            'high_memory_events': 0,
            'high_cpu_events': 0,
            'gc_calls': 0,
            'start_time': time.time()
        }
    
    async def start_monitoring(self):
        """Start resource monitoring"""
        self.running = True
        logging.info(f"🔍 Resource monitor started (limit: {self.memory_limit/1024/1024:.0f}MB)")
        
        while self.running:
            try:
                await self._check_resources()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Resource monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _check_resources(self):
        """Check current resource usage"""
        # Memory check
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        # CPU check
        cpu_percent = self.process.cpu_percent(interval=1)
        
        # Thread count
        thread_count = self.process.num_threads()
        
        # Log warning if limits exceeded
        if memory_info.rss > self.memory_limit:
            self.stats['high_memory_events'] += 1
            logging.warning(f"⚠ Memory high: {memory_mb:.1f}MB (> {self.memory_limit/1024/1024:.0f}MB)")
            
            # Force garbage collection
            gc.collect()
            self.stats['gc_calls'] += 1
            
            # Clear asyncio tasks if too many
            tasks = len(asyncio.all_tasks())
            if tasks > 100:
                logging.warning(f"  Too many tasks: {tasks}, forcing cleanup")
                # Can't cancel tasks here, just warning
        
        if cpu_percent > self.cpu_limit:
            self.stats['high_cpu_events'] += 1
            logging.warning(f"⚠ CPU high: {cpu_percent}% (> {self.cpu_limit}%)")
        
        # Periodic stats (every 5 minutes)
        elapsed = time.time() - self.stats['start_time']
        if elapsed > 300 and int(elapsed) % 300 < self.check_interval:
            logging.info(
                f"📊 Resource stats: CPU={cpu_percent}%, "
                f"Memory={memory_mb:.1f}MB, "
                f"Threads={thread_count}, "
                f"Tasks={len(asyncio.all_tasks())}"
            )
    
    def get_stats(self):
        """Get monitoring statistics"""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_human': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m",
            'current_memory_mb': self.process.memory_info().rss / (1024 * 1024),
            'current_cpu_percent': self.process.cpu_percent(),
            'current_threads': self.process.num_threads()
        }
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logging.info("🛑 Resource monitor stopped")
        logging.info(f"📊 Final stats: {self.get_stats()}")

# Global instance
resource_monitor = ResourceMonitor()

