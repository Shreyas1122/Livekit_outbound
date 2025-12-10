import csv
import os
import platform
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from pymongo import AsyncMongoClient

from dispatcher import OutboundCallDispatcher
from agent import router as call_router


app = FastAPI(title="VisionIT Voice Agent API")


app.include_router(call_router)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://shreyas:shreyas@shreyas.8rxrw.mongodb.net/?retryWrites=true&w=majority&appName=shreyas")
DB_NAME = os.getenv("DB_NAME", "Calls")
COLLECTION = os.getenv("COLLECTION", "Total_calls")

BASE_DIR = Path(__file__).resolve().parent
PYTHON_BIN = Path(sys.executable)

worker_process: Optional[subprocess.Popen] = None

mongo_client = AsyncMongoClient(MONGODB_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION]


@app.post("/worker/start")
def start_worker(mode: str = "dev"):
    """
    Launch the LiveKit worker that runs `agent.py`.
    Returns existing status if already running.
    """
    global worker_process

    if worker_process and worker_process.poll() is None:
        return {"status": "already_running", "pid": worker_process.pid}

    cmd = [str(PYTHON_BIN), "agent.py"]
    if mode:
        cmd.append(mode)

    worker_process = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdout=sys.stdout,  # log to current process output
        stderr=sys.stderr,
        text=True,
        start_new_session=True,  # allow killing the whole group on POSIX
    )

    return {"status": "worker_started", "pid": worker_process.pid, "cmd": cmd}


@app.post("/worker/stop")
def stop_worker():
    """
    Stop the running LiveKit worker process if present.
    """
    global worker_process

    if not worker_process or worker_process.poll() is not None:
        worker_process = None
        return {"status": "no_worker_running"}

    pid = worker_process.pid

    # First try a graceful terminate
    worker_process.terminate()

    try:
        worker_process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        # If still alive, escalate per-OS
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # send signal to the whole process group
            try:
                os.killpg(pid, signal.SIGKILL)
            except Exception:
                worker_process.kill()

        try:
            worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    worker_process = None

    return {"status": "worker_stopped", "pid": pid}


@app.get("/worker/status")
def worker_status():
    """
    Report whether the LiveKit worker is running.
    """
    if worker_process and worker_process.poll() is None:
        return {"status": "running", "pid": worker_process.pid}
    return {"status": "stopped"}



# ---------------------------
#  Request Models
# ---------------------------

class SingleCallRequest(BaseModel):
    phone_number: str
    caller_id: str = "VisionIT Sales"


class BulkCallRequest(BaseModel):
    phone_numbers: list[str]
    caller_id: str = "VisionIT Sales"


# ---------------------------
#  Single Outbound Call Route
# ---------------------------
@app.post("/call")
async def call_single(req: SingleCallRequest):
    dispatcher = OutboundCallDispatcher()

    result = await dispatcher.make_call(
        req.phone_number,
        caller_id=req.caller_id
    )

    response = {
        "success": result.get("success", False),
        "room_name": result.get("room_name"),
        "phone_number": result.get("phone_number"),
        "error": result.get("error")
    }

    # If call initiation succeeded — insert a record into MongoDB
    if result.get("success"):
        # Prepare a document to insert — you can add more fields as needed
        doc = {
            "phone_number": req.phone_number,
            "caller_id": req.caller_id,
            "room_name": result.get("room_name"),
            "timestamp": __import__("datetime").datetime.utcnow(),
            # add any other metadata/results
        }
        # try:
        #     insert_result = await collection.insert_one(doc)  # Async insert
        #     response["mongo_id"] = str(insert_result.inserted_id)
        # except Exception as e:
        #     # Log error — but still return API success/failure
        #     response["mongo_error"] = str(e)

    return response


# ---------------------------
#  Bulk Outbound Calls Route
# ---------------------------
@app.post("/bulk-calls")
async def call_bulk(req: BulkCallRequest):
    dispatcher = OutboundCallDispatcher()

    results = await dispatcher.make_bulk_calls(
        req.phone_numbers,
        caller_id=req.caller_id
    )

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    return {
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "results": results
    }




@app.post("/datacomes")
async def datacomes(name :str,email: str,phone: int):
    print("api is execured successfuly bhai ")
    with open("C:\\appontments\\Appointments.csv", "a", newline="") as f:
     writer = csv.writer(f)
     writer.writerow([name,email,phone])
    return {"status": "API is running",
            "value": email}