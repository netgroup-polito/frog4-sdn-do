while :;do ping -n -w1 -W1 -c1 130.192.225.241| grep -E "rtt|100%"| sed -e "s/^/`date` /g"; sleep 1; done
