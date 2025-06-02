from sqlalchemy.orm import Session
from datetime import datetime
from app import models, schemas

def create_team(db: Session, team: schemas.TeamCreate):
    db_team = models.Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def create_service(db: Session, service: schemas.ServiceCreate):
    db_service = models.Service(name=service.name)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def create_script(db: Session, script: schemas.ScriptCreate):
    db_script = models.Script(
        name=script.name,
        filename=script.filename,
        team_id=script.team_id,
        service_id=script.service_id,
        file_content=script.file_content,
        description=script.description,
        is_deleted=script.is_deleted,
        uploaded_at=datetime.utcnow()
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    return db_script

def create_test_run(db: Session, run: schemas.TestRunCreate):
    db_run = models.TestRun(
        script_id=run.script_id,
        users=run.users,
        spawn_rate=run.spawn_rate,
        run_time=run.run_time,
        env=run.env,
        status="created",
        started_at=datetime.now(),
        web_port=run.web_port
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run