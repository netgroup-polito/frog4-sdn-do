#!/bin/sh
ifconfig h4-eth0 down
ifconfig h4-eth0 up
ifconfig h4-eth0 20.0.0.11/24
route add default gw 20.0.0.254
