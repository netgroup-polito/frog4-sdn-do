#!/bin/bash
./install_ovsdbrest_onos.sh
./install_appscap_onos.sh
sleep 2
./start_sdn-do.sh

