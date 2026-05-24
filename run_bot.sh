#!/bin/bash
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
python3 -m pip install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt
echo "🤖 Starting Anonka bot..."
python3 -m backend.app.main
