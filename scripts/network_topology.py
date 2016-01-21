'''
Created on Gen 14, 2015

@author: giacomoratta

This script print the network topology detected by OpenDayLight Domain Orchestrator.

'''

import logging

# Configuration Parser
from odl_do.config import Configuration

# NetGraph
from odl_do.netgraph import NetGraph

# Configuration
conf = Configuration()
conf.log_configuration()


# START OPENDAYLIGHT DOMAIN ORCHESTRATOR
logging.debug("Printing the network topology watched by OpenDayLight Domain Orchestrator")
print("OpenDayLight Domain Orchestrator - Network Topology")

print("\nOpenDayLight version: "+Configuration().ODL_VERSION+"\n")

ng = NetGraph(Configuration().ODL_VERSION, Configuration().ODL_ENDPOINT, Configuration().ODL_USERNAME, Configuration().ODL_PASSWORD)
nt = ng.getNetworkTopology()

for node in nt:
    print("\n  Node:        "+node['node'])
    print("--------------------------------------------------")
    print("  neighbours:", end="")
    for nb in node['neighbours']:
        print("  "+nb)
        print("             ",end="")
    print("")



    
