import os
from fastapi import FastAPI
from app.routes import scripts, teams, services, test_runs
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Performance Testing API")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("app/static/index.html") as f:
        return f.read()

# Ensure scripts directory exists on startup
@app.on_event("startup")
def startup_event():
    os.makedirs("scripts", exist_ok=True)

app.include_router(scripts.router)
app.include_router(teams.router)
app.include_router(services.router)
app.include_router(test_runs.router)

@app.get("/")
def root():
    return {"message": "Welcome to Performance Testing API"}