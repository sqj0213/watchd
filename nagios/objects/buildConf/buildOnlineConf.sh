#!/bin/sh
rm -f  /etc/nagios/objects/buildConf/platform-monitor.cfg
rm -f  /etc/nagios/objects/buildConf/platform-monitor-ip.cfg
rm -f  /etc/nagios/objects/buildConf/platform-monitor-idc.cfg
rm -f  /etc/nagios/objects/buildConf/platform-monitor-idc-group.cfg
rm -f  /etc/nagios/objects/buildConf/platform-monitor-host-group.cfg
#生成测试ip列表
/usr/bin/php /etc/nagios/objects/buildConf/build_v1.php
cp /etc/nagios/objects/buildConf/platform-monitor.cfg /etc/nagios/objects/
cp /etc/nagios/objects/buildConf/platform-monitor-ip.cfg /etc/nagios/objects/
cp /etc/nagios/objects/buildConf/platform-monitor-idc.cfg /etc/nagios/objects/
cp /etc/nagios/objects/buildConf/platform-monitor-host-group.cfg /etc/nagios/objects/
cp /etc/nagios/objects/buildConf/platform-monitor-idc-group.cfg /etc/nagios/objects/
nagios -v  /etc/nagios/nagios.cfg >>/tmp/nagiosTest.log
service nagios restart


