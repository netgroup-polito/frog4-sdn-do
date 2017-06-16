#!/bin/sh
ifconfig h1-eth0 down
ifconfig h1-eth0 up
route add default gw 10.0.0.254
tc qdisc add dev h1-eth0 root netem delay 0.250ms rate 1Gbit
