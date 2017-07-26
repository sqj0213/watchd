#!/bin/env python
#coding=utf8
"""
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3
"""
#debug开关，需要更多日志时改为True
debugFlag=True
#线程间共用，是否要退出状态
stopFlag=False
"""

openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits
stats.openapi.blossomin_yf.byhost.10_75_0_53.total._2_remind_set_count_json.hits

openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_500ms
openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_1s

stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.less_500ms
"""
#ip列表
ipList=set()
#ip对应的接口dict
ipApiList={}
#nagios的响应值
returnCode={"WARNING":1,"OK":0,"CRITICAL":2,"UnKnown":3}
#告警阀值
threshold={"httpStatusCodeFailedRate":0.10, 
           "httpResponseTimeAreaUpper1s":0.10,
           "httpResponseTimeAreaUpper2s":0.10,
           "httpStatusCodeFailedRate_warning":0.05, 
           "httpResponseTimeAreaUpper1s_warning":0.05,
           "httpResponseTimeAreaUpper2s_warning":0.05,

           }

def setTimeFlag( _logObj=None ):
    _logObj.info( "timer is set timeFlag true" )
    timeFlag = True
