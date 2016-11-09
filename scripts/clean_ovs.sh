#! /bin/bash
#REMOVE BRDIGES
sudo ovs-vsctl show | grep Bridge | awk {'print $2'} | cut -d '"' -f 2 | while read b ; do sudo ovs-vsctl del-br $b; done