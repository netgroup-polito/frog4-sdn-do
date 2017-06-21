#!/bin/bash
#./set_ip.sh
ddbroker -r tcp://*:5555 -k broker-keys.json -s /0/0/0/ -l d
