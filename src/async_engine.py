import os
import re
import time
import httpx
import asyncio
import sqlite3
from multiprocessing import Pool, cpu_count
from memory_profiler import memory_usage

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "data", "server.log")
DB_FILE = os.path.join(BASE_DIR, "data", "logs_optimized.db")
WEBHOOK_URL = "https://httpbin.org/post"

LOG_REGEX = re.compile(
    r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[^\s]+" (?P<status>\d+) (?P<bytes>\d+)'
)

def process_chunk_worker(file_position, chunk_size):
    local_error_count, local_line_count = 0, 0
    records = []
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        f.seek(file_position)
        bytes_read = 0
        if file_position != 0:
            bytes_read += len(f.readline().encode('utf-8'))
            
        while bytes_read < chunk_size:
            line = f.readline()
            if not line: break
            bytes_read += len(line.encode('utf-8'))
            local_line_count += 1
            
            match = LOG_REGEX.match(line)
            if match:
                data = match.groupdict()
                status = int(data["status"])
                if status >= 500:
                    local_error_count += 1
                records.append((data["ip"], data["timestamp"], data["method"], data["endpoint"], status, int(data["bytes"])))
                
    if records:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO log_metrics (ip, timestamp, method, endpoint, status, bytes) VALUES (?, ?, ?, ?, ?, ?)", records)
        conn.commit()
        conn.close()
        
    return local_line_count, local_error_count

async def send_async_alert(error_total):
    payload = {"text": f"🚨 Error spike! {error_total:,} errors found."}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(WEBHOOK_URL, json=payload, timeout=2.0)
            return res.status_code == 200
        except Exception: return False

def run_pipeline():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS log_metrics")
    c.execute("CREATE TABLE log_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, timestamp TEXT, method TEXT, endpoint TEXT, status INTEGER, bytes INTEGER)")
    conn.commit()
    conn.close()

    num_workers = cpu_count()
    file_size = os.path.getsize(LOG_FILE)
    chunk_size = file_size // num_workers
    chunks = [(i * chunk_size, chunk_size) for i in range(num_workers)]
    
    with Pool(processes=num_workers) as pool:
        results = pool.starmap(process_chunk_worker, chunks)
        
    total_lines = sum(r[0] for r in results)
    total_errors = sum(r[1] for r in results)
    print(f"Processed: {total_lines:,} lines | Errors: {total_errors:,}")
    
    if total_errors > 10000:
        alert_start = time.time()
        asyncio.run(send_async_alert(total_errors))
        print(f"⚡ Async Alert Delivered in {(time.time() - alert_start)*1000:.2f} ms")

if __name__ == "__main__":
    start_time = time.time()
    mem_use = memory_usage(run_pipeline, interval=0.05)
    duration = time.time() - start_time
    print(f"⏱️  Execution Time: {duration:.2f} seconds")
    print(f"📈 Peak RAM Usage: {max(mem_use) - min(mem_use):.2f} MB")