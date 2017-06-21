#! /bin/bash

#useful link:
#	http://www.cyberciti.biz/faq/howto-debian-ubutnu-set-default-gateway-ipaddress/

#Assign the ip address to user port 
ifconfig eth1 10.0.0.254/24
#Assign the ip address to wan port using the dhcp server
ifconfig eth0 20.0.0.254/24
#cp /sbin/dhclient /usr/sbin/dhclient && /usr/sbin/dhclient eth0 -v 

#start the SSH server
#service ssh start
#echo "ssh service started"

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

ifconfig
