#!/bin/env python
#coding=utf8
import argparse,sys

parser = argparse.ArgumentParser()
parser.add_argument("--flag", type=str, default="local and remote test turn/off", help="please input online or /(OK,WARNING,CRITICAL,UNKNOWN,PENDING)" )
parser.add_argument("--appkey", type=str, default="2123530299", help="please input check app key default key 2123530299" )
parser.add_argument("--statusCode", type=float, default=403, help="please input app key check failed code default 403)" )
parser.add_argument("--alertFailedRate", type=float, default=0.30, help="please input app key check failed rate)" )
args = parser.parse_args()
#HTTP WARNING: HTTP/1.1 401 Authorization Required - page size 721 too large - 721 bytes in 0.001 second response time |time=0.000549s;;;0.000000 size=721B;12;0;0
resultTmpl="HTTP_CHECK _STATUS_:_NOTE1_ - _NOTE2_ failed rate _RATE_ - upper 1 seconds _RATE1_ - upper 2 seconds _RATE2_|_IP__INTERFACE_ time=_AVGTIME_"
def getHttpResult( _status, _appkey, _statusCode, _failedRate ):
	if ( _status == "online" ):
		#取remote的数值来决定"
		_status = "OK"
	rate1=0.25
	success=30
	failed=20
	avgTime=0.05
	return "APPKEY_CHECK %s:appkey failed rate %f|time=%fs,success=%d,failed=%d"%(_status,rate1,avgTime,success,failed)


print getHttpResult(args.flag, args.appkey, args.statusCode, args.alertFailedRate)
