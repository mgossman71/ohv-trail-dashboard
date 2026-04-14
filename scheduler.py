"""
scheduler.py — OHV Trail Dashboard scraper scheduler

Runs as a long-lived process inside the Docker 'ohv-scraper' service.
Executes scraper.py immediately on startup, then sleeps and repeats on the
configured interval.

Configuration (set via environment variable in docker-compose.yml):
    SCRAPE_INTERVAL_HOURS   How often to scrape, in whole hours (default: 12).
                            Cannot be set below MIN_INTERVAL_HOURS (12).
                            Minimum is enforced to avoid overloading the DNR website.

Usage:
    Normally started by Docker:  python scheduler.py
    Manual one-off scrape:       python scraper.py
"""

import os
import time
import subprocess
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEXT_SCRAPE_FILE = os.environ.get(
    'NEXT_SCRAPE_FILE',
    os.path.join(BASE_DIR, 'data', 'next_scrape.txt')
)

MIN_INTERVAL_HOURS = 12  # Hard floor — do not lower. Respects the DNR website.
_requested = int(os.environ.get('SCRAPE_INTERVAL_HOURS', '12'))
INTERVAL_HOURS = max(MIN_INTERVAL_HOURS, _requested)
if _requested < MIN_INTERVAL_HOURS:
    print(f"[scheduler] WARNING: SCRAPE_INTERVAL_HOURS={_requested} is below the minimum of "
          f"{MIN_INTERVAL_HOURS}. Using {MIN_INTERVAL_HOURS} hours instead.", flush=True)
INTERVAL_SECONDS = INTERVAL_HOURS * 3600
SCRAPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraper.py')


def run_scraper():
    """Invoke scraper.py as a subprocess and log the outcome."""
    print(f"\n[scheduler] Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    result = subprocess.run([sys.executable, SCRAPER], capture_output=False)
    if result.returncode != 0:
        print(f"[scheduler] Scraper exited with code {result.returncode}", flush=True)
    else:
        print(f"[scheduler] Scrape finished successfully", flush=True)


if __name__ == '__main__':
    print(f"[scheduler] Starting — will scrape every {INTERVAL_HOURS} hour(s)", flush=True)
    while True:
        run_scraper()
        next_run = datetime.fromtimestamp(time.time() + INTERVAL_SECONDS)
        # Write the next run time so the dashboard can show a countdown
        try:
            with open(NEXT_SCRAPE_FILE, 'w') as f:
                f.write(next_run.strftime('%Y-%m-%dT%H:%M:%S') + '\n')
        except Exception as e:
            print(f"[scheduler] Could not write next scrape time: {e}", flush=True)
        print(f"[scheduler] Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        time.sleep(INTERVAL_SECONDS)
