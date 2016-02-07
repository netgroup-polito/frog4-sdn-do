'''
Created on Gen 14, 2015

@author: giacomoratta

This script print the network topology detected by Network Controller Domain Orchestrator.

'''

import logging

# Configuration Parser
from do_core.config import Configuration

# NetManager
from do_core.netmanager import NetManager

# Configuration
conf = Configuration()
conf.log_configuration()


# START NETWORK CONTROLLER DOMAIN ORCHESTRATOR
logging.debug("Printing the network topology watched by Network Controller Domain Orchestrator")
print("Network Controller Domain Orchestrator - Network Topology")


ng = NetManager()
nt = ng.getNetworkTopology()

print("\nNetwork Controller: "+ng.getControllerName()+"\n")

for node in nt:
    print("\n  Node:        "+node['node'])
    print("--------------------------------------------------")
    print("  neighbours:", end="")
    for nb in node['neighbours']:
        print("  "+nb)
        print("             ",end="")
    print("")



    
