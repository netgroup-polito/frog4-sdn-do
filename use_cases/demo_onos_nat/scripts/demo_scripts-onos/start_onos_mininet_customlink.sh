#!/bin/bash
cd ~/git-repositories/onos/tools/dev/mininet
sudo mn --link tc,bw=1000,deelay=0.3ms --custom onos.py --controller onos,1 --topo tree,2,2
echo DONE
