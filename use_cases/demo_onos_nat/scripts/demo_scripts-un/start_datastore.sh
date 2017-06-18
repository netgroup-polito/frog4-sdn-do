#!/bin/bash
cd ~/git-repositories/un-orchestrator/datastore/
source .env/bin/activate
python manage.py runserver --d config/datastore_config.ini
