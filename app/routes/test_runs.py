from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import crud, schemas, models
import subprocess, time, datetime
import tempfile
import os
import requests
from fastapi.responses import Response

router = APIRouter(prefix="/runs", tags=["Test Runs"])
test_processes = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def monitor_process(run_id):
    try:
        proc = test_processes[run_id]["process"]
        proc.wait()
        if test_processes.__contains__(run_id):
            end_time = time.time()
            test_processes[run_id]["end_time"] = end_time
            temp_file = test_processes[run_id].get("temp_file")  # Get the temp file path

            # Update DB with completion time
            db = SessionLocal()
            try:
                test_run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
                if test_run:
                    test_run.completed_at = datetime.datetime.fromtimestamp(end_time)
                    test_run.status = "completed"
                    duration = end_time - test_processes[run_id]["start_time"]
                    test_run.duration_seconds = duration
                    db.commit()
                    test_processes.pop(run_id, None)
            finally:
                db.close()
    finally:
        if test_processes.__contains__(run_id):
            if temp_file:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass


@router.post("/")
def create_test_run(run: schemas.TestRunCreate, db: Session = Depends(get_db)):
    return crud.create_test_run(db, run)


@router.get("/", response_model=list[schemas.TestRun])
def list_test_runs(db: Session = Depends(get_db)):
    return db.query(models.TestRun).all()


@router.get("/currently-running", response_model=list[schemas.TestRun])
def get_runs_for_script(db: Session = Depends(get_db)):
    runs = (
        db.query(
            models.TestRun,
            models.Script.name.label("script_name"),
            models.Script.filename.label("filename"),
            models.TestRun.env.label("environment"),
        )
        .join(models.Script, models.TestRun.script_id == models.Script.id)
        .filter(models.TestRun.status == "running")
        .all()
    )
    return [
        schemas.TestRun(
            id=run.TestRun.id,
            script_id=run.TestRun.script_id,
            users=run.TestRun.users,
            spawn_rate=run.TestRun.spawn_rate,
            env=run.environment,
            script_name=run.script_name,
            filename=run.filename,
            status=run.TestRun.status,
            started_at=run.TestRun.started_at.strftime("%d-%m-%y %H:%M") if run.TestRun.started_at else None,
            completed_at=run.TestRun.completed_at.strftime("%d-%m-%y %H:%M") if run.TestRun.completed_at else None,
            web_port=run.TestRun.web_port
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=schemas.TestRun)
def get_test_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="TestRun not found")
    return run


@router.post("/start-test")
def start_test(run: schemas.TestRunCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == run.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    # Check if the port is already in use
    if run.web_port and any(proc["web_port"] == run.web_port for proc in test_processes.values()):
        raise HTTPException(status_code=400, detail="Web port already in use")

    test_run = crud.create_test_run(db, run)

    # Create a temporary file with a custom name
    temp_file_name = f"{test_run.id}_{script.filename}.py"
    temp_file_path = os.path.join(tempfile.gettempdir(), temp_file_name)
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(script.file_content)

    cmd = [
        "locust",
        "-f", temp_file_path,
        "--host", "http://example.com",
        "-u", str(run.users),
        "-r", str(run.spawn_rate),
        "--run-time", run.run_time or "1m",
        "--web-port", str(run.web_port or 8089)
    ]
    proc = subprocess.Popen(cmd)
    start_time = time.time()
    test_processes[test_run.id] = {
        "process": proc,
        "start_time": start_time,
        "end_time": None,
        "web_port": run.web_port,
        "temp_file": temp_file_path  # Store the temp file path
    }

    background_tasks.add_task(monitor_process, test_run.id)
    test_run.status = "running"
    db.commit()
    return {"message": "Test started", "run_id": test_run.id}


@router.post("/stop-test/{run_id}")
def stop_test(run_id: int):
    entry = test_processes.get(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Test run not found or already stopped")

    web_port = entry.get("web_port")
    if not web_port:
        raise HTTPException(status_code=400, detail="Web port not found for the test run")

    try:
        # Step 1: Call Locust stop API
        stop_response = requests.get(f"http://localhost:{web_port}/stop")
        if stop_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to stop the test via Locust")

        # Step 2: Download the HTML report
        time.sleep(5)  # Wait for Locust to generate the report
        report_url = f"http://localhost:{web_port}/stats/report?download=1&theme=light"
        report_response = requests.get(report_url)
        if report_response.status_code == 200:
            report_content = report_response.content

            # Store the report in the database
            db = SessionLocal()
            try:
                test_run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
                if test_run:
                    test_run.report_blob = report_content
                    test_run.completed_at = datetime.datetime.now()
                    test_run.status = "completed"
                    db.commit()
            finally:
                db.close()
        else:
            raise HTTPException(status_code=500, detail="Failed to download the report from Locust")

        # Step 3: Terminate the subprocess
        proc = entry["process"]
        if proc.poll() is None:
            proc.terminate()
        temp_file = test_processes[run_id].get("temp_file")
        if temp_file:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        test_processes.pop(run_id, None)
        return {"message": "Test stopped gracefully, report saved", "run_id": run_id}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error stopping test: {str(e)}")


@router.get("/script/{script_id}", response_model=list[schemas.TestRun])
def get_runs_for_script(script_id: int, db: Session = Depends(get_db)):
    runs = (
        db.query(
            models.TestRun,
            models.Script.name.label("script_name"),
            models.Script.filename.label("filename"),
            models.TestRun.env.label("environment"),
        )
        .join(models.Script, models.TestRun.script_id == models.Script.id)
        .filter(models.TestRun.script_id == script_id)
        .all()
    )
    return [
        schemas.TestRun(
            id=run.TestRun.id,
            script_id=run.TestRun.script_id,
            users=run.TestRun.users,
            spawn_rate=run.TestRun.spawn_rate,
            env=run.environment,
            script_name=run.script_name,
            filename=run.filename,
            status=run.TestRun.status,
            started_at=run.TestRun.started_at.strftime("%d-%m-%y %H:%M") if run.TestRun.started_at else None,
            completed_at=run.TestRun.completed_at.strftime("%d-%m-%y %H:%M") if run.TestRun.completed_at else None,
            web_port=run.TestRun.web_port
        )
        for run in runs
    ]


@router.get("/status/{run_id}")
def test_status(run_id: int, db: Session = Depends(get_db)):
    test_run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return {
        "run_id": test_run.id,
        "status": test_run.status,
        "started_at": test_run.started_at,
        "completed_at": test_run.completed_at
    }


@router.get("/{run_id}/report")
def download_report(run_id: int, db: Session = Depends(get_db)):
    test_run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
    if not test_run or not test_run.report_blob:
        raise HTTPException(status_code=404, detail="Report not found for the specified test run")

    return Response(
        content=test_run.report_blob,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{run_id}.html"}
    )
