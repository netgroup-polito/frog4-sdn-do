#!/bin/bash
echo "" > FrogDomainOrchestrator.log
python3 gunicorn_start.py "$@"
