from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import crud, schemas, models
import os
import shutil
from fastapi.responses import StreamingResponse
from io import BytesIO

UPLOAD_DIR = "scripts"

router = APIRouter(prefix="/scripts", tags=["Scripts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Script])
def list_scripts(db: Session = Depends(get_db)):
    scripts = db.query(models.Script).filter(models.Script.is_deleted == False).all()
    for script in scripts:
        script.team_name = script.team.name if script.team else "N/A"
        script.service_name = script.service.name if script.service else "N/A"
    return scripts


@router.get("/{script_id}", response_model=schemas.Script)
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(
        models.Script.id == script_id , models.Script.is_deleted == False
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post("/")
def upload_script(
        name: str = Form(...),
        description: str = Form(""),
        team_id: int = Form(None),
        service_id: int = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    file_content = file.file.read()

    script_data = schemas.ScriptCreate(
        name=name,
        filename=file.filename,
        team_id=team_id,
        service_id=service_id,
        file_content=file_content,
        description=description,
        is_deleted=False
    )
    return crud.create_script(db, script_data)


@router.get("/{script_id}/download")
def download_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    return StreamingResponse(
        BytesIO(script.file_content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={script.filename}"}
    )

@router.put("/{script_id}")
def update_script(
        script_id: int,
        name: str = Form(None),
        description: str = Form(None),
        team_id: int = Form(None),
        service_id: int = Form(None),
        file: UploadFile = File(None),
        db: Session = Depends(get_db)
):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if name:
        script.name = name
    if description:
        script.description = description
    if team_id is not None:
        script.team_id = team_id
    if service_id is not None:
        script.service_id = service_id
    if file:
        script.filename = file.filename
        script.file_content = file.file.read()

    db.commit()
    db.refresh(script)
    return {"message": "Script updated successfully", "script": script}


@router.delete("/{script_id}")
def delete_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    script.is_deleted = True  # Mark as deleted
    db.commit()
    return {"message": "Script marked as deleted successfully"}