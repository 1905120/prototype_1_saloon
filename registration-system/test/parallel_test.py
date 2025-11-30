import json
import time
import httpx
import os
url = "http://localhost:8000/api/v1/makerequest"
script_dir = os.path.dirname(os.path.abspath(__file__))
file_name = "clients_100.json"

with open(f'{script_dir}\\{file_name}') as f:
    rec = json.load(f)

with httpx.Client() as client:  # persistent connection
    times = []
    for idx, payload in enumerate(rec, 1):
        start = time.perf_counter()
        res = client.post(url, json=payload)
        end = time.perf_counter()
        times.append((end-start)*1000)
        print(f"Request {idx}: {(end-start)*1000:.2f} ms")

    print(f"Average: {sum(times)/len(times):.2f} ms")
