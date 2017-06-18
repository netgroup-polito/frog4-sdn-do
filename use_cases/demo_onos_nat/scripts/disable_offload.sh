
# while true
# do
#        sleep 2
        for i in `ls /sys/class/net`



        do
                if [ $i != lo  ]
                then
                        ethtool -K $i tx off
                        ethtool -K $i gso off
                        ethtool -K $i gro off
                        ethtool -K $i tso off
                fi
        done
# done
