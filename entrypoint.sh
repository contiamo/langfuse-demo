#!/bin/sh
set -e

echo "Running DB migrations..."
rag-migrate

echo "Starting app..."
exec uvicorn rag.app:app --host 0.0.0.0 --port 7932
