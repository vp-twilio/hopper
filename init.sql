-- === Table: teams ===
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- === Table: services ===
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- === Table: scripts ===
CREATE TABLE IF NOT EXISTS scripts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    team_id INT REFERENCES teams(id) ON DELETE SET NULL,
    service_id INT REFERENCES services(id) ON DELETE SET NULL,
    file_content BYTEA NOT NULL,
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(name, team_id, service_id)
);

-- === Table: test_runs ===
CREATE TABLE IF NOT EXISTS test_runs (
    id SERIAL PRIMARY KEY,
    script_id INT REFERENCES scripts(id) ON DELETE CASCADE,
    users INT NOT NULL,
    spawn_rate INT NOT NULL,
    run_time VARCHAR(50),               -- Optional run-time string, e.g., '30s'
    env VARCHAR(50) DEFAULT 'default',  -- e.g., staging, prod
    web_port INT DEFAULT 8089,         -- Port for web service
    status VARCHAR(20) DEFAULT 'created', -- created, running, completed
    result_summary TEXT,
    report_url TEXT,                    -- e.g., S3 URL to HTML report
    duration_seconds INT,               -- How long the test actually ran (optional)
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    report_blob BYTEA            -- Optional binary report blob
);

CREATE INDEX IF NOT EXISTS idx_scripts_team_service ON scripts(team_id, service_id);
CREATE INDEX IF NOT EXISTS idx_runs_script_id ON test_runs(script_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON test_runs(status);

INSERT INTO teams (name) VALUES ('PNIP'), ('LC');
INSERT INTO services (name) VALUES ('PNJS'), ('IFS');