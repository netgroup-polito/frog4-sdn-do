'''
Created on Gen 14, 2015

@author: giacomoratta

This script print the network topology watched by OpenDayLight Domain Orchestrator.

'''

import logging, json

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

print("\nOpenDayLight version: "+conf.ODL_VERSION+"\n")

payload = json.loads('{"username":"admin", "password":"admin"}', 'utf-8')

ng = NetGraph(conf.ODL_VERSION, conf.ODL_ENDPOINT, conf.ODL_USERNAME, conf.ODL_PASSWORD)
nt = ng.getNetworkTopology()

for node in nt:
    print("\n  Switch:      "+node['node'])
    print("--------------------------------------------------")
    print("  neighbours:", end="")
    for nb in node['neighbours']:
        print("  "+nb)
        print("             ",end="")
    print("")



    
