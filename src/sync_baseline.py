import sqlite3
import re
import time
import os
from memory_profiler import memory_usage

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data", "server.log")
DB_FILE = os.path.join(BASE_DIR, "data", "logs_baseline.db")

LOG_REGEX = re.compile(
    r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[^\s]+" (?P<status>\d+) (?P<bytes>\d+)'
)

def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS log_metrics")
    cursor.execute("""
        CREATE TABLE log_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, timestamp TEXT, method TEXT, endpoint TEXT, status INTEGER, bytes INTEGER
        )
    """)
    conn.commit()
    return conn

def process_logs_sync():
    conn = setup_database()
    cursor = conn.cursor()
    error_count, total_lines = 0, 0
    batch_size = 50000
    batch = []
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            match = LOG_REGEX.match(line)
            if match:
                data = match.groupdict()
                status = int(data["status"])
                if status >= 500:
                    error_count += 1
                batch.append((data["ip"], data["timestamp"], data["method"], data["endpoint"], status, int(data["bytes"])))
                
                if len(batch) >= batch_size:
                    cursor.executemany("INSERT INTO log_metrics (ip, timestamp, method, endpoint, status, bytes) VALUES (?, ?, ?, ?, ?, ?)", batch)
                    batch = []
    if batch:
        cursor.executemany("INSERT INTO log_metrics (ip, timestamp, method, endpoint, status, bytes) VALUES (?, ?, ?, ?, ?, ?)", batch)
    conn.commit()
    conn.close()
    print(f"Processed: {total_lines:,} lines | Errors: {error_count:,}")

if __name__ == "__main__":
    start_time = time.time()
    mem_use = memory_usage(process_logs_sync, interval=0.1)
    duration = time.time() - start_time
    print(f"⏱️  Execution Time: {duration:.2f} seconds")
    print(f"📈 Peak RAM Usage: {max(mem_use) - min(mem_use):.2f} MB")