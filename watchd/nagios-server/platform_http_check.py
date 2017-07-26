#!/bin/env python
#coding=utf8
import argparse,sys

parser = argparse.ArgumentParser()
parser.add_argument("--checkType", type=str, default="stdout", help="please input check type(monitor check machine, machine push check info to monitor)" )
parser.add_argument("--checkResult", type=str, default="", help="please input check result" )
parser.add_argument("--ip", type=str, default="10.210.238.147", help="please input ip" )
parser.add_argument("--flag", type=str, default="local and remote test turn/off", help="please input online or /(OK,WARNING,CRITICAL,UNKNOWN,PENDING)" )
parser.add_argument("--api", type=str, default="/feed", help="please input http check uri" )
parser.add_argument("--alertFailedRate", type=float, default=0.30, help="please input http failed alert rate(!200/200)" )
parser.add_argument("--warningtimeout", type=int, default=1, help="please input http slow request time long ")
parser.add_argument("--errortimeout", type=int, default=3, help="please input http slow request time long ")
args = parser.parse_args()
#HTTP WARNING: HTTP/1.1 401 Authorization Required - page size 721 too large - 721 bytes in 0.001 second response time |time=0.000549s;;;0.000000 size=721B;12;0;0
resultTmpl="HTTP_CHECK _STATUS_:_NOTE1_ - _NOTE2_ failed rate _RATE_ - upper 1 seconds _RATE1_ - upper 2 seconds _RATE2_|_IP__INTERFACE_ time=_AVGTIME_"
def getHttpResult( _ip, _interface, _alertFailedRate, _warningTimeout, _errorTimeOut,_status ):
	if ( _status == "online" ):
		#取remote的数值来决定"
		_status = "OK"
	rate1=0.25
	rate2=0.09
	rate3=0.09
	avgTime=0.05
	return "HTTP_CHECK %s:http 200 status code failed rate %f - upper 1s %f - upper 3s %f|time=%fs"%(_status,rate1,rate2,rate3,avgTime)

if ( args.checkType == "stdout" ):
	print args.checkResult
else:	
	print getHttpResult(args.ip, args.api, args.alertFailedRate, args.warningtimeout, args.errortimeout,args.flag)
