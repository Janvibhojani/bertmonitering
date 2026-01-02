# simple_monitor.py
import psutil
import time
import os

print("🖥️  SIMPLE PERFORMANCE MONITOR")
print("Press Ctrl+C to stop")
print("-" * 50)

try:
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # System
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        
        print(f"📊 SYSTEM:")
        print(f"  CPU: {cpu}%")
        print(f"  Memory: {mem.percent}% ({mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB)")
        
        # Find scraper process
        scraper_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmd = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if any(word in cmd.lower() for word in ['scraper', 'flask', 'run.py']):
                        scraper_pid = proc.info['pid']
                        p = psutil.Process(scraper_pid)
                        
                        print(f"\n🎯 SCRAPER (PID:{scraper_pid}):")
                        print(f"  CPU: {p.cpu_percent(interval=0.1):.1f}%")
                        print(f"  Memory: {p.memory_info().rss/1024**2:.1f}MB")
                        print(f"  Threads: {p.num_threads()}")
                        break
            except:
                continue
        
        # Browser processes
        browsers = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                name = proc.info['name'].lower()
                if any(b in name for b in ['chrome', 'chromium', 'msedge']):
                    browsers.append(proc.info)
            except:
                continue
        
        print(f"\n🌐 BROWSERS ({len(browsers)}):")
        total_browser_cpu = sum(b['cpu_percent'] for b in browsers)
        total_browser_mem = sum(b['memory_percent'] for b in browsers)
        print(f"  Total CPU: {total_browser_cpu:.1f}%")
        print(f"  Total Memory: {total_browser_mem:.1f}%")
        
        # Show top 3
        for b in browsers[:3]:
            print(f"  - {b['name']}: CPU={b['cpu_percent']:.1f}%, MEM={b['memory_percent']:.1f}%")
        
        print(f"\n⏱️  {time.strftime('%H:%M:%S')}")
        print("-" * 50)
        print("Refreshing in 5 seconds...")
        
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\n🛑 Monitoring stopped")