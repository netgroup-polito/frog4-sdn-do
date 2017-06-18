#!/bin/bash
cd ~/onos/tools/dev/mininet
sudo mn --custom onos.py --controller onos,1 --topo tree,2,2
echo DONE
