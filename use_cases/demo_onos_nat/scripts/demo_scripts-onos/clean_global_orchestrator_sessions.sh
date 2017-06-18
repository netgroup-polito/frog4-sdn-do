#!/bin/bash
cd ~/git-repositories/frog4-orchestrator/scripts
mysql -u root -p orchestrator < db_clean_session.sql
