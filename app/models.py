from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, LargeBinary, Boolean
from sqlalchemy.orm import relationship
from app.db import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Script(Base):
    __tablename__ = "scripts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filename = Column(String, nullable=False)
    file_content = Column(LargeBinary, nullable=False)  # Store file as binary data
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    description = Column(Text, nullable=True)
    uploaded_at = Column(TIMESTAMP)
    is_deleted = Column(Boolean, default=False)  # 0 for not deleted, 1 for deleted

    team = relationship("Team", backref="scripts")
    service = relationship("Service", backref="scripts")

class TestRun(Base):
    __tablename__ = "test_runs"
    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    users = Column(Integer)
    spawn_rate = Column(Integer)
    run_time = Column(String, nullable=True)
    env = Column(String, default="default")
    web_port = Column(Integer, nullable=True)
    status = Column(String, default="created")
    result_summary = Column(Text, nullable=True)
    report_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    report_blob = Column(LargeBinary, nullable=True)

    script = relationship("Script", backref="test_runs")