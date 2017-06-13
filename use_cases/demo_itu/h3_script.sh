#!/bin/sh
ifconfig h3-eth0 down
ifconfig h3-eth0 up
ifconfig h3-eth0 20.0.0.10/24
route add default gw 20.0.0.254
