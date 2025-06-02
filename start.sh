#!/bin/sh
/usr/bin/tini -- /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &"