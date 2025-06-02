from pydantic import BaseModel
from typing import Optional

class TeamCreate(BaseModel):
    name: str

class ServiceCreate(BaseModel):
    name: str

class ScriptCreate(BaseModel):
    name: str
    filename: str
    team_id: Optional[int] = None
    service_id: Optional[int] = None
    file_content: bytes
    description: Optional[str] = None
    is_deleted: bool

class TestRunCreate(BaseModel):
    script_id: int
    users: int
    spawn_rate: int
    run_time: Optional[str] = None
    env: Optional[str] = "default"
    web_port: Optional[int] = None

class Team(TeamCreate):
    id: int

    class Config:
        orm_mode = True

class Service(ServiceCreate):
    id: int

    class Config:
        orm_mode = True

class Script(ScriptCreate):
    id: int
    team_name: Optional[str] = None
    service_name: Optional[str] = None

    class Config:
        orm_mode = True

class TestRun(TestRunCreate):
    id: int
    script_name: Optional[str] = None
    filename: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        orm_mode = True