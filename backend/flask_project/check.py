# check.py - ULTRA SIMPLE DIAGNOSTIC
import psutil
import time
import os

def main():
    print("🔍 QUICK SYSTEM CHECK")
    print("=" * 50)
    
    # System info
    cpu_percent = psutil.cpu_percent(interval=2)
    memory = psutil.virtual_memory()
    
    print(f"💻 SYSTEM:")
    print(f"  CPU Usage: {cpu_percent}%")
    print(f"  Memory: {memory.percent}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")
    print(f"  Available: {memory.available/1024**3:.1f}GB")
    
    # Find Python processes
    print(f"\n🐍 PYTHON PROCESSES:")
    python_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmd = ' '.join(proc.info['cmdline'][:3]) if proc.info['cmdline'] else ''
                python_procs.append({
                    'pid': proc.info['pid'],
                    'cmd': cmd,
                    'proc': proc
                })
        except:
            continue
    
    for i, p in enumerate(python_procs[:10]):  # Show first 10
        try:
            cpu = p['proc'].cpu_percent(interval=0.1)
            mem_mb = p['proc'].memory_info().rss / (1024**2)
            threads = p['proc'].num_threads()
            
            print(f"  {i+1}. PID:{p['pid']} - CPU:{cpu:.1f}%, Mem:{mem_mb:.1f}MB, Threads:{threads}")
            print(f"     Command: {p['cmd'][:80]}...")
        except:
            print(f"  {i+1}. PID:{p['pid']} - [Access denied]")
    
    # Find Chrome/Chromium processes
    print(f"\n🌐 BROWSER PROCESSES:")
    browser_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            name = proc.info['name'].lower()
            if any(browser in name for browser in ['chrome', 'chromium', 'msedge']):
                browser_procs.append(proc.info)
        except:
            continue
    
    print(f"  Total browser processes: {len(browser_procs)}")
    
    if browser_procs:
        total_cpu = sum(p['cpu_percent'] for p in browser_procs)
        total_mem = sum(p['memory_percent'] for p in browser_procs)
        print(f"  Total browser CPU: {total_cpu:.1f}%")
        print(f"  Total browser Memory: {total_mem:.1f}%")
        
        # Show top 5
        for i, p in enumerate(browser_procs[:5]):
            print(f"    {i+1}. {p['name']} (PID:{p['pid']}): CPU={p['cpu_percent']:.1f}%, MEM={p['memory_percent']:.1f}%")
    
    print(f"\n📊 PROCESS COUNT SUMMARY:")
    print(f"  Total processes: {len(psutil.pids())}")
    print(f"  Python processes: {len(python_procs)}")
    print(f"  Browser processes: {len(browser_procs)}")
    
    print(f"\n⚠️  CHECKING FOR ISSUES:")
    
    issues = []
    if cpu_percent > 70:
        issues.append(f"High CPU usage: {cpu_percent}%")
    if memory.percent > 80:
        issues.append(f"High memory usage: {memory.percent}%")
    if len(browser_procs) > 10:
        issues.append(f"Too many browser processes: {len(browser_procs)}")
    
    if issues:
        print("  ❌ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ No major issues detected")
    
    print(f"\n" + "=" * 50)
    print("📈 For real-time monitoring, run this again in 30 seconds")
    print("=" * 50)

if __name__ == "__main__":
    main()