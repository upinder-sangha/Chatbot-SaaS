import json
import os
from datetime import datetime, timezone
from threading import Lock

TRACKING_FILE = "db/user_records.json"
lock = Lock()

def log_upload(email, bot_id, filename, name):
    data = {
        "email": email,
        "bot_id": bot_id,
        "filename": filename,
        "name": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    lock.acquire()
    try:
        if not os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, "w") as f:
                json.dump([data], f, indent=2)
        else:
            with open(TRACKING_FILE, "r+") as f:
                existing = json.load(f)
                existing.append(data)
                f.seek(0)
                json.dump(existing, f, indent=2)
    finally:
        lock.release()