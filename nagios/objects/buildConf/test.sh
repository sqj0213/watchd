#!/bin/sh
rm -f  platform-monitor.cfg
#生成测试ip列表
echo ""|awk '{for (i=1;i<2;i++) for (j=1;j<2;j++)print "openapi.blossomin_yf"j".byhost.201_76_1_"i}'  >./ipList
#生成测试接口
echo ""|awk '{for (i=1;i<2;i++) print "_2_counter_get_count_json"i}' >./apiList
php ./build.php
cp ./platform-monitor.cfg ../
nagios -v  /etc/nagios/nagios.cfg
