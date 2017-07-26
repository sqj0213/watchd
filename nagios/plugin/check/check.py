#!/bin/env python
#coding=utf8
import pdb,datetime
from time import strftime
import os,threading,time,json,sys
from lib import include as globalVariable
'''
1）N台服务器非200状态码监控：(N>=1)
单一状态码，1分钟内，比例达正常请求30%以上报警。
2）N台服务器N个下行接口性能超过1s监控。(N>=1)
N台服务器，N个下行接口，1分钟内，性能超过1s比例达10%以上报警。
3）N台服务器N个上行接口性能超过3s监控。(N>=1)
N台服务器，N个上行接口，1分钟内，性能超过3s比例达10%以上报警。
4)单一appkey 403状态码监控：
单一appkey，1分钟内，比例达正常请求30%以上报警。
'''
class check():

    redisObj = None
    logObj = None
    warningTimeOut=0.10
    errorTimeOut=0.10
    alertFailedRate=0.30
    alertResponsetNum = 20
    conf=None
    key=None
    key_type=None
    ipList = None
    ipApiList = None
    mergeData = None
    keyNumCount = 0
    def __init__( self,  _logObj=None,_redisObj=None, _conf=None, _key=None, _type=None):
        self.logObj = _logObj
        self.redisObj = _redisObj
        self.alertFailedRate = _conf['config']['successfailedrate']
        self.warningTimeOut = _conf['config']['responsetimeareaupper1rate']
        self.errorTimeOut = _conf['config']['responsetimeareaupper2rate']
        self.alertResponsetNum = int(_conf['config']['responsetnum'])
        self.conf = _conf
        self.key = _key
        self.key_type = _type

    def getRemoteData( self, _keyList=[] ):
        retDict = {}
        redisRetList = self.redisObj.mget( _keyList )
        for i in range( len(_keyList) ):
            if not redisRetList[i]:
                retDict[_keyList[i]] = 0
            else:
                retDict[_keyList[i]] = float(redisRetList[i])
        return retDict
    
    def buildData(self):
        #pdb.set_trace()
        dic = {}
        #单接口
        if self.key_type == "api":
            #pdb.set_trace()
            ip=self.key[0:self.key.rindex(".")]
            api=self.key[self.key.rindex(".")+1:]
            dic = {"key":ip,"api":"."+api}
        #单机
        elif self.key_type == "ip":
            ip = self.key
            dic = {"key":ip,"api":""}
        #单池子
        elif self.key_type == "idc":
            idc = self.key
            dic = {"key":idc,"api":""}
        return dic


    def start(self):

        self.ipList = globalVariable.ipList
        self.ipApiList = globalVariable.ipApiList
        #pdb.set_trace()
        self.logObj.info('nagios active check key:%s type:%s is started!'%(self.key,self.key_type))
        if self.key and self.key_type:
            self.logObj.info('nagios active check key:%s type:%s start buildData'%(self.key,self.key_type))
            result = self.check(self.buildData())
            print result["msg"]
            sys.exit(int(result["code"]))

        else:
            self.logObj.info('nagios active check not ip or not interface')

    def check(self, _data):
        _ip = _data["key"]
        _interface = _data["api"]
        #单机单接口总数key
        total_hits = "%s.total%s.hits"%( _ip, _interface)
        #单机单接口成功数key
        http2xx_hits = "%s.http_2xx%s.hits"%( _ip, _interface)
        #单机响应小于500mskey
        less_500ms = "%s.http_2xx%s.less_500ms"%( _ip, _interface)
        #单机响应小于1skey
        less_1s = "%s.http_2xx%s.less_1s"%( _ip, _interface)
        #单机响应小于2skey
        less_2s = "%s.http_2xx%s.less_2s"%( _ip, _interface)
        #单机响应小于4skey
        less_4s = "%s.http_2xx%s.less_4s"%( _ip, _interface)
        #单机响应大于4skey
        over_4s = "%s.http_2xx%s.over_4s"%( _ip, _interface)
        #单机平均响应时间key
        mean = "%s.http_2xx%s.mean"%(_ip, _interface)
        #单机单接口4xx数key
        http4xx_hits = "%s.http_4xx%s.hits"%( _ip, _interface)
        #单机单接口5xx数key
        http5xx_hits = "%s.http_5xx%s.hits"%( _ip, _interface)
        #从redis请求数据
        requestKeyDict= [total_hits,http2xx_hits,less_500ms,less_1s,less_2s,less_4s,over_4s,mean,http4xx_hits,http5xx_hits]
        #pdb.set_trace()
        returnResult = self.getRemoteData( requestKeyDict )
        #返回给nagios的缺省值
        rate1=0
        rate2=0
        rate3=0
        _status = "STATE_OK"
        #返回的数据结果：key:value
        avgTime = returnResult[mean]
        #聚合所有2xx
        tmpTotal = returnResult[less_500ms] + returnResult[less_1s] + returnResult[less_2s] + returnResult[less_4s] + returnResult[over_4s]

        #redis数据不准确, 2xx = less500 + less1s + less2s + less_4s + over_4s
        if returnResult[http2xx_hits] != tmpTotal:
            returnResult[http2xx_hits] = tmpTotal

        #redis数据不准确，total = 2xx + 4xx + 5xx
        if returnResult[total_hits] < returnResult[http2xx_hits]:
            returnResult[total_hits] = returnResult[http2xx_hits] + returnResult[http4xx_hits] + returnResult[http5xx_hits]
        
        #http2xx_hits=0 total_hits =0 status = unknown
        if (returnResult[http2xx_hits] == returnResult[total_hits] == 0):
            _status = "STATE_UNKNOWN"
            self.logObj.info("key:%s type:%s total_hits:%d http2xx_hits:%d less_500ms:%d less_1s:%d less_2s:%d less_4s:%d over_4s:%d avgTime:%d"%(self.key, self.key_type, returnResult[total_hits], returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult[less_4s], returnResult[over_4s], avgTime))

            retMsg = globalVariable.logTemplate%(_status, returnResult[total_hits], returnResult[http2xx_hits], returnResult[http4xx_hits], returnResult[total_hits], rate1*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[http2xx_hits], rate2*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult[http2xx_hits], rate3*100, avgTime )
            
            self.logObj.info("key:%s type:%s exit:%s code:%s msg:%s"%(self.key, self.key_type, self.conf["status"][_status.lower()], _status, retMsg ))
            return {"code":self.conf["status"][_status.lower()],"msg":retMsg}


        if (returnResult[total_hits] < self.alertResponsetNum):
            _status = "STATE_OK"
            self.logObj.info("key:%s type:%s total_hits:%d http2xx_hits:%d less_500ms:%d less_1s:%d less_2s:%d less_4s:%d over_4s:%d avgTime:%d"%(self.key, self.key_type, returnResult[total_hits], returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult['less_4s'], returnResult['over_4s'], avgTime))

            retMsg = globalVariable.logTemplate%(_status, returnResult[total_hits], returnResult[http2xx_hits], returnResult[http4xx_hits], returnResult[total_hits], rate1*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[http2xx_hits], rate2*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult[http2xx_hits], rate3*100, avgTime )
            
            self.logObj.info("key:%s type:%s exit:%s code:%s msg:%s"%(self.key, self.key_type, self.conf["status"][_status.lower()], _status, retMsg ))
            return {"code":self.conf["status"][_status.lower()],"msg":retMsg}


        #非200请求所在比例
        if ( returnResult[total_hits] > 1 and (returnResult[total_hits]-returnResult[http2xx_hits]) > 1 ):
            
            rate1=(returnResult[total_hits]-returnResult[http2xx_hits]-returnResult[http4xx_hits])/returnResult[total_hits]

         #超过1秒的请求比例
        if ( tmpTotal > 1 and (tmpTotal-returnResult[less_500ms]-returnResult[less_1s]) > 1 ):
           
            rate2=(tmpTotal-returnResult[less_500ms]-returnResult[less_1s])/tmpTotal
        
        #超过2秒的请求比例
        if ( tmpTotal > 1 and (tmpTotal-returnResult[less_500ms]-returnResult[less_1s]-returnResult[less_2s]) > 1 ):
            
            rate3=(tmpTotal-returnResult[less_500ms]-returnResult[less_1s]-returnResult[less_2s])/tmpTotal

        if ( rate1 > float(self.alertFailedRate) or rate2 > float(self.warningTimeOut) or rate3 > float(self.errorTimeOut) ):
            _status = "STATE_CRITICAL"
        else:
            _status = "STATE_OK"

        self.logObj.info("key:%s type:%s total_hits:%d http2xx_hits:%d less_500ms:%d less_1s:%d less_2s:%d less_4s:%d over_4s:%d avgTime:%d"%(self.key, self.key_type, returnResult[total_hits], returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult[less_4s], returnResult[over_4s], avgTime))

        retMsg = globalVariable.logTemplate%(_status, returnResult[total_hits], returnResult[http2xx_hits], returnResult[http4xx_hits], returnResult[total_hits], rate1*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[http2xx_hits], rate2*100, returnResult[http2xx_hits], returnResult[less_500ms], returnResult[less_1s], returnResult[less_2s], returnResult[http2xx_hits], rate3*100, avgTime )

        #retMsg = "HTTP_CHECK %s:http 200 status code failed rate((4xx+5xx/total)) %f - upper 1s (>1s/2xx)%f - upper 3s(>3s/2xx)%f | time = %fs"%(_status,rate1,rate2,rate3,avgTime)
        self.logObj.info("key:%s type:%s exit:%s code:%s msg:%s"%(self.key, self.key_type, self.conf["status"][_status.lower()], _status, retMsg ))
        return {"code":self.conf["status"][_status.lower()],"msg":retMsg}
