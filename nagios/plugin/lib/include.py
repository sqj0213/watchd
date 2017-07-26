#!/bin/env python
#coding=utf8
#ip列表
ipList=set()
#ip对应的接口dict
ipApiList={}
#debug开关，需要更多日志时改为True
debugflag=True
#log日志模板
logTemplate = "%s: unhttp2xx( (total:%d-2xx:%d-4xx:%d)/total:%d ) = %.2f%%; upper1s( (2xx:%d - <500:%d - <1s:%d)/2xx:%d) = %.2f%%; upper2s( (2xx:%d - <500:%d - <1s:%d - <2s:%d)/2xx:%d) = %.2f%% | avgTime = %f"

