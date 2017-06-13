#!/bin/bash
echo "" > FrogDomainOrchestrator.log
python3 start_gunicorn.py "$@"
