#!/bin/env python
#coding=utf8
import logging as logObj
from pystatsd import Client;
import argparse;
import time
import socket


parser = argparse.ArgumentParser()
parser.add_argument("--idc", type=str, default="openapi.coreapi_sh", help="please input idc in the key default openapi.coreapi_sh" )
parser.add_argument("--ip", type=str, default="8_8_8_8", help="please input ip in the key default 1_1_1_1" )
parser.add_argument("--log", type=str, default="./test_statsd.log", help="please input log path default ./test_statsd.log" )
args = parser.parse_args()

logPath = args.log
ipKey = args.ip
idcKey = args.idc
apiKeyList = ["_","_2_","_2_statuses_count_json","_2_statuses_count_sp_json","_2_statuses_friends_timeline_ids_json","_2_statuses_friends_timeline_json","_2_statuses_mix_user_timeline_json","_2_statuses_repost_json"]

def interKey(_idc,_ip):
    requstList = []
    for _api in apiKeyList:
        string_byhost = ""
        #byhost
        byhost_total_hits = "%s.byhost.%s.total.%s.hits:1|c\n"%(_idc,_ip,_api)
        byhost_total_hits = byhost_total_hits*7
        byhost_http_2xx = "%s.byhost.%s.http_2xx.%s.hits:1|c\n"%(_idc,_ip,_api)
        byhost_http_2xx = byhost_http_2xx*5

        byhost_http_5xx = "%s.byhost.%s.http_5xx.%s.hits:1|c\n"%(_idc,_ip,_api)
        byhost_http_4xx = "%s.byhost.%s.http_4xx.%s.hits:1|c\n"%(_idc,_ip,_api)
        byhost_less_500ms = "%s.byhost.%s.http_2xx.%s.less_500ms:1|c\n"%(_idc,_ip,_api)
        byhost_less_1s = "%s.byhost.%s.http_2xx.%s.less_1s:1|c\n"%(_idc,_ip,_api)
        byhost_less_2s = "%s.byhost.%s.http_2xx.%s.less_2s:1|c\n"%(_idc,_ip,_api)
        byhost_less_4s = "%s.byhost.%s.http_2xx.%s.less_4s:1|c\n"%(_idc,_ip,_api)
        byhost_over_4s = "%s.byhost.%s.http_2xx.%s.over_4s:1|c\n"%(_idc,_ip,_api)
        string_byhost = byhost_total_hits + byhost_http_2xx + byhost_http_5xx + byhost_http_4xx + byhost_less_500ms + byhost_less_1s + byhost_less_2s +byhost_less_4s + byhost_over_4s
        requstList.append(string_byhost)

        string_byhost1 = ""
        #not byhost  #openapi.blossomin_yf.http_2xx._2_remind_set_count_json.hits
        total_hits = "%s.total.%s.hits:1|c\n"%(_idc,_api)
        total_hits = total_hits*7

        http_2xx = "%s.http_2xx.%s.hits:1|c\n"%(_idc,_api)
        http_2xx = http_2xx*5

        http_5xx = "%s.http_5xx.%s.hits:1|c\n"%(_idc,_api)
        http_4xx = "%s.http_4xx.%s.hits:1|c\n"%(_idc,_api)
        less_500ms = "%s.http_2xx.%s.less_500ms:1|c\n"%(_idc,_api)
        less_1s = "%s.http_2xx.%s.less_1s:1|c\n"%(_idc,_api)
        less_2s = "%s.http_2xx.%s.less_2s:1|c\n"%(_idc,_api)
        less_4s = "%s.http_2xx.%s.less_4s:1|c\n"%(_idc,_api)
        over_4s = "%s.http_2xx.%s.over_4s:1|c\n"%(_idc,_api)

        string_byhost1 =  total_hits + http_2xx  + http_5xx + http_4xx + less_500ms + less_1s + less_2s + less_4s + over_4s
        requstList.append(string_byhost1)
    return requstList

#timers.openapi.blossomin_yf.byhost.10_75_0_53.http2xx._2_remind_set_count_json.mean 500
def timeKey(_idc,_ip):
    requstList = ""
    for _api in apiKeyList:
        #byhost
        byhost_timer_mean = "%s.byhost.%s.http_2xx.%s:500.000000|ms\n"%(_idc,_ip,_api)
        timer_mean = "%s.http_2xx.%s:500.000000|ms\n"%(_idc,_api)
        requstList += byhost_timer_mean+timer_mean
    return requstList

def init_log():
    logObj.basicConfig(filename=logPath,filemode='a+',level=logObj.INFO, format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s %(filename)s %(module)s %(lineno)d', datefmt='%Y-%m-%d %H:%M:%S' )
    return logObj   

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
logObj = init_log()
requestList = interKey(idcKey,ipKey)
string_timer = timeKey(idcKey,ipKey)
count_num = 0
logObj.info("start to send data to statsd!")
time_flag = time.time()
while True:
    count_num += 1
    for key in requestList:
        sock.sendto(key,('10.13.240.137',8333))
    sock.sendto(string_timer,('10.13.240.137',8333))
    if count_num%10 == 0:
        time.sleep(1)
    if count_num%1000 == 0:
        logObj.info("A total of %d data has been sent use time %f"%(count_num,time.time()-time_flag))
        time_flag = time.time()
# clientObj.increment( key )

