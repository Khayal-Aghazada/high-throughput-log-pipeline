import datetime
import os
import random
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE_NAME = os.path.join(DATA_DIR, "server.log")

TOTAL_LINES = 20_000  # Scaled for premium stress testing
CHUNK_SIZE = 100_000     

IP_POOL = [f"192.168.1.{random.randint(1, 254)}" for _ in range(50)] + \
          [f"10.0.0.{random.randint(1, 254)}" for _ in range(30)] + \
          ["8.8.8.8", "1.1.1.1"]

METHODS = ["GET", "POST", "PUT", "DELETE"]
ENDPOINTS = ["/api/v1/users", "/api/v1/auth/login", "/api/v1/products", "/dashboard", "/checkout"]
STATUS_CODES = [200] * 80 + [304] * 5 + [404] * 10 + [500] * 4 + [503] * 1

def generate_log_file():
    print(f"Generating {TOTAL_LINES:,} log lines inside data/ folder...")
    start_time = time.time()
    current_timestamp = datetime.datetime.now()
    lines_written = 0

    with open(LOG_FILE_NAME, "w", encoding="utf-8") as f:
        chunk = []
        for _ in range(TOTAL_LINES):
            current_timestamp += datetime.timedelta(milliseconds=random.randint(10, 500))
            timestamp_str = current_timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
            
            ip = random.choice(IP_POOL)
            method = random.choice(METHODS)
            endpoint = random.choice(ENDPOINTS)
            status = random.choice(STATUS_CODES)
            body_bytes = random.randint(120, 4500) if status == 200 else random.randint(20, 500)
            
            log_line = f'{ip} - - [{timestamp_str}] "{method} {endpoint} HTTP/1.1" {status} {body_bytes}\n'
            chunk.append(log_line)
            
            if len(chunk) >= CHUNK_SIZE:
                f.writelines(chunk)
                lines_written += len(chunk)
                chunk = []
                
        if chunk:
            f.writelines(chunk)

    print(f"Success! Time taken: {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    generate_log_file()