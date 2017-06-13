## Run Mininet and ONOS

In order to run ONOS on top of a mininet network, you need to use the onos.py script provided in this folder.

1. Copy the provided onos.py into the ONOS_ROOT/tools/dev/mininet/ folder (replace the older)

2. Copy in the same folder also all the hosts scripts (h*_script.sh), needed to set up the networking of each mininet host

3. Run both Mininet and ONOS using the command:

	$ sudo mn --custom onos.py --controller onos,1 --topo tree,2,2

4. Once you are in the mininet CLI, run all scripts for each client:

	> h1 h1_script.sh
	> h2 h2_script.sh
	> h3 h3_script.sh
	> h4 h4_script.sh

## Install applications on ONOS

...
