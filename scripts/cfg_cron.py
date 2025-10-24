import time
import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv
import schedule

load_dotenv()

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "")
CFG_PATH = os.environ.get("CFG_PATH", "")
CFG_YAML_PATH = os.environ.get("OST_CONFIG_PATH", "")

if not os.path.isabs(CFG_PATH):
    CFG_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, CFG_PATH))
if not os.path.isabs(CFG_YAML_PATH):
    CFG_YAML_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, CFG_YAML_PATH))

print(f"[CRON] Using config script path: {CFG_PATH}")
print(f"[CRON] Target YAML path: {CFG_YAML_PATH}")

# Function to run the config generation script
def run_cfg():
    print("\n[CRON] ===============================")
    print(f"[CRON] Cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[CRON] Executing: python {CFG_PATH}")
    
    result = subprocess.run(["python", CFG_PATH], capture_output=True, text=True)
    print(f"[CRON] cfg.py exited with code {result.returncode}")
    if result.stdout:
        print(f"[CRON] Output:\n{result.stdout}")
    if result.stderr:
        print(f"[CRON] Errors:\n{result.stderr}")
    # Check if the YAML config file was generated
    if os.path.exists(CFG_YAML_PATH):
        mtime = datetime.fromtimestamp(os.path.getmtime(CFG_YAML_PATH)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[CRON] Config YAML generated: {CFG_YAML_PATH} (last modified: {mtime})")
    else:
        print(f"[CRON] Config YAML NOT FOUND: {CFG_YAML_PATH}")
    print(f"[CRON] Cycle finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[CRON] ===============================\n")

# Schedule the job every day at 03:00
schedule.every().day.at("03:00").do(run_cfg)

print("[CRON] Waiting for scheduled time (03:00)...")

while True:
    schedule.run_pending()
    time.sleep(30)