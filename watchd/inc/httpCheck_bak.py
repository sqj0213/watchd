#!/bin/env python
#coding=utf8
from time import strftime
import os,threading,time,json
from inc import include as globalVariable

#HTTP WARNING: HTTP/1.1 401 Authorization Required - page size 721 too large - 721 bytes in 0.001 second response time |time=0.000549s;;;0.000000 size=721B;12;0;0

#check_platform_interface!stats.openapi.blossomin_yf.byhost.10_75_0_1!_2_counter_get_count_json10
#成功数/失败比统计：
#     单机成功/失败比：(指标1)
#     单机单接口成功量：
#          stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits(非200的用total做差即可)
#
#     单机单接口总量：
#          stats.openapi.blossomin_yf.byhost.10_75_0_53.total._2_remind_set_count_json.hits--------不紧急
#
#     全量成功/失败比：(指标2)
#
#     单接口成功总量
#          stats.openapi.blossomin_yf.http_2xx._2_remind_set_count_json.hits(非200的用total做差即可)
#     单接口总量
#          stats.openapi.blossomin_yf.total._2_remind_set_count_json.hits
#响应时间区间分布统计：
"""
一期规划：
1）N台服务器非200状态码监控：(N>=1)
单一状态码，1分钟内，比例达正常请求30%以上报警。
2）N台服务器N个下行接口性能超过1s监控。(N>=1)
N台服务器，N个下行接口，1分钟内，性能超过1s比例达10%以上报警。
3）N台服务器N个上行接口性能超过3s监控。(N>=1)
N台服务器，N个上行接口，1分钟内，性能超过3s比例达10%以上报警。
4)单一appkey 403状态码监控：
单一appkey，1分钟内，比例达正常请求30%以上报警。
二期规划：
1）N台服务器N个资源性能超监控。(N>=1)
N台服务器N个资源性能异常、失败异常。性能异常为当前性能指标，失败异常为链接异常等。

          单机单接口响应时间区间：(指标3)
          单机单接口
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_500ms
          单机单接口总量(以下5个值相加)
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_500ms
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_1s
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_2s
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_4s
               stats.openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.over_4s

          全量响应时间区间：(指标4)
          单接口总量：
               stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.less_500ms
               stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.less_1s
               stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.less_2s
               stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.less_4s
               stats.openapi.blossomin_yf.http_2xx._2_counter_get_count_json.over_4s

平均响应时间统计
     单机单接口各状态码量：
          stats.timers.openapi.blossomin_yf.byhost.10_75_0_53.http2xx._2_remind_set_count_json.mean(10s)
          stats.timers.openapi.blossomin_yf.byhost.10_75_0_53.http2xx._2_remind_set_count_json.count(10s请求总数)

     全量单接口响应时间平均量：
          stats.timers.openapi.blossomin_yf.http_2xx._2_remind_set_count_json.mean--------不紧急
"""
class httpCheck(  ):

    redisObj = None
    logObj = None
    warningTimeOut=0.10
    errorTimeOut=0.10
    alertFailedRate=0.30
    nscaTmpl=""
    stopFlag=False
    conf=None
    retMsgIP=""
    idcInfo={}
    coreIdc={}
    everyM=1

    def __init__( self,  _logObj=None,_redisObj=None, _conf=None ):
        self.logObj = _logObj
        self.redisObj = _redisObj
        self.alertFailedRate = globalVariable.threshold["httpStatusCodeFailedRate"]
        self.warningTimeOut = globalVariable.threshold["httpResponseTimeAreaUpper1s"]
        self.errorTimeOut = globalVariable.threshold["httpResponseTimeAreaUpper2s"]
        self.nscaTmpl = _conf['template']['nscamsgtmpl']
        self.conf = _conf
        self.stopFlag=False
        #创建IDC信息
        self.idcInfo=eval(_conf['IDC']['idc'])
        self.everyM=int(_conf['config']['everym'])

    def getRemoteData( self, _keyList=[] ):
        retDict = {}
        redisRetList = self.redisObj.mget( _keyList )
        for i in range( len(_keyList) ):
            if not redisRetList[i]:
                retDict[_keyList[i]] = 0
            else:
                retDict[_keyList[i]] = float(redisRetList[i])
        return retDict

    def buildNagiosData(self,_nagiosTempFile=None):
        fileHandler = None
        ipCount=0
        apiTotalCount=0
        apiAlertCount=0
        apiOKCount=0
        okFilterCount=0
        for ip in globalVariable.ipList:
            ipCount = ipCount + 1
            apiCount=0
            try:
                apiListSet = globalVariable.ipApiList[ip]
            except:
                continue
            for api in apiListSet:
                apiCount = apiCount + 1
                serviceName = "%s.%s"%( ip, api )
                checkResult = self.check( ip, api )
                if checkResult:
                    nscaTmplStr = self.nscaTmpl.replace('_SERVICENAME_', serviceName)
                    #nscamsgtmpl="localhost;_SERVICENAME_;_STATUSCODE_;_MSG_"
                    nscaTmplStr = nscaTmplStr.replace( '_STATUSCODE_', str(checkResult['retCode']))
                    nscaTmplStr = nscaTmplStr.replace( '_MSG_', checkResult['retMsg'])
                    if not fileHandler:
                        fileHandler = open( _nagiosTempFile, 'a+')
                    ipCount=0
                    fileHandler.write( "%s\n"%(nscaTmplStr))
                else:
                    okFilterCount = okFilterCount + 1
                if checkResult['retCode'] == 0:
                    apiOKCount = apiOKCount + 1
                else:
                    apiAlertCount = apiAlertCount + 1
                apiCount = apiCount + 1
            self.logObj.info('ip(%s) apiCount(%d)'%(ip, apiCount))
            apiTotalCount = apiTotalCount + apiCount
            checkIPResult=self.mergeIPData(ip)
            if checkIPResult:
                nscaTmplStr = self.nscaTmpl.replace('_SERVICENAME_', ip)
                #nscamsgtmpl="localhost;_SERVICENAME_;_STATUSCODE_;_MSG_"
                nscaTmplStr = nscaTmplStr.replace( '_STATUSCODE_', str(checkIPResult['retCode']))
                nscaTmplStr = nscaTmplStr.replace( '_MSG_', checkIPResult['retMsgIP'])
                if not fileHandler:
                    fileHandler = open( _nagiosTempFile, 'a+')
                fileHandler.write( "%s\n"%(nscaTmplStr))
            else:
                pass
                #okFilterCount = okFilterCount + 1
        for idcName in self.coreIdc.keys():
            #调用IDC合并函数
            checkIDCResult=self.mergeIDCData(idcName)
            if checkIDCResult:
                nscaTmplStr = self.nscaTmpl.replace('_SERVICENAME_', idcName)
                #nscamsgtmpl="localhost;_SERVICENAME_;_STATUSCODE_;_MSG_"
                nscaTmplStr = nscaTmplStr.replace( '_STATUSCODE_', str(checkIDCResult['retCode']))
                nscaTmplStr = nscaTmplStr.replace( '_MSG_', checkIDCResult['retMsgIDC'])
                if not fileHandler:
                    fileHandler = open( _nagiosTempFile, 'a+')
                fileHandler.write( "%s\n"%(nscaTmplStr))
        if fileHandler:
            fileHandler.flush()
            fileHandler.close()
        self.logObj.info('build nagios template file(%s) complete ipCount(%d) apiTotalCount(%d) apiAlertCount(%d) apiOKCount(%d) okFilterCount(%d)'%(_nagiosTempFile,ipCount,apiTotalCount,apiAlertCount,apiOKCount,okFilterCount))

    def sendNSCAData(self):
        timerStr = strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
        #tempfilepath="/data0/log/statsd/send-nagios-"
        nagiosTempFile = "%s-%s.ini"%(self.conf['nagios']['tempfilepath'], timerStr)
        self.logObj.info('build nagios data begin!')
        self.buildNagiosData(nagiosTempFile)
        if os.path.isfile( nagiosTempFile ):
            self.logObj.info('build nagios data end!')
            sendCmd = self.conf['nagios']['sendnagioscmd']
            sendCmd = sendCmd.replace('_NAGIOSTEMPFILE_', nagiosTempFile)
            sendCmd = "%s%s"%(sendCmd,self.conf['nagios']['sendnagioslogpath'])
            startTime=time.time()
            cmdRetCode = os.system( sendCmd )
            useTIme=int(time.time()-startTime)
            if cmdRetCode != 0:
                self.logObj.info( "send nsca server failed(%s) retCode(%d),useTime=%ds"%(sendCmd,cmdRetCode,useTIme))
            else:
                self.logObj.info( "send nsca server success(%s) retCode(%d),useTIme=%ds"%(sendCmd,cmdRetCode,useTIme))
            if globalVariable.debugFlag == False:
                deleteFileStr1 = "/bin/rm -f %s"%(nagiosTempFile)
                #windows下运行修改
                os.system(deleteFileStr1)
                deleteFileStr2 = "/bin/rm -f %s"%(self.conf['nagios']['sendnagioslogpath'])
                #为windows下运行修改
                os.system(deleteFileStr2)
            self.logObj.info("send info success!!!")
        else:
            self.logObj.info("build nagios file is not exists(%s)"%(nagiosTempFile))

    def run(self):
        time.sleep(3)
        threadname = threading.currentThread().getName()
        self.logObj.info('httpCheck (%s) thread started!'%(threadname))
        while True:
            if globalVariable.stopFlag == True:
                self.logObj.info("httpCheck (%s) thread stoped!"%(threadname))
                break
            self.logObj.info('brpop queue(%s) and blocktime(%s)'%(self.conf['queue']['queuekeyname'], self.conf['queue']['blocktimerout']))
            queueNodeTuple=self.redisObj.brpop(self.conf['queue']['queuekeyname'], int(self.conf['queue']['blocktimerout']))

            self.stopFlag=False
            if queueNodeTuple:
                queueNode = json.loads( queueNodeTuple[1] )
                #time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(queueNode))
                queueNodeTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(queueNode[0]/1000))
                self.logObj.info("queueNode time(%s) countKeyCount(%d) timerKeyCount(%d) and send nagios data begin!"%(queueNodeTime,queueNode[1],queueNode[2]) )
                self.sendNSCAData()
                self.logObj.info("queueNode time(%s) countKeyCount(%d) timerKeyCount(%d) and send nagios data end!"%(queueNodeTime,queueNode[1],queueNode[2]) )
            else:
                self.logObj.info('queue is null!')
            self.stopFlag=True

    #合并单机的监控指标
    def mergeIPData(self,_ip):
        #单机的各个维度的累加值
        sumSuccessHit=0
        sumSuccessLess500=0
        sumSuccessLess1s=0
        sumSuccessLess2s=0
        sumSuccessLess4s=0
        sumSuccessOver4s=0
        sumTotalHitKey=0
        sumSuccessMeanKey=0
        sumTotal5xx=0
        #单机成功数key
        successHitsKey1 = "%s.total_less.hits"%( _ip)
        #单机总数key
        totalHitsKey2 = "%s.total_hits.hits"%( _ip)
        #单机5xx总数key
        totalHite5xx = "%s.http_5xx.hits"%(_ip)
        #返回给nagios的缺省值
        _status = "OK"
        #单机响应时间区间key
        successLessKey1 = "%s.http_2xx.less_500ms"%( _ip)
        successLessKey2 = "%s.http_2xx.less_1s"%( _ip)
        successLessKey3 = "%s.http_2xx.less_2s"%( _ip)
        successLessKey4 = "%s.http_2xx.less_4s"%( _ip)
        successLessKey5 = "%s.http_2xx.over_4s"%( _ip)
        #单机平均响应时间key
        successMeanKey = "%s.http_2xx.mean"%(_ip)
        #向远端发送请求的key列表
        requestKeyDict= [successHitsKey1,totalHitsKey2,successLessKey1,successLessKey2,successLessKey3,successLessKey4,successLessKey5,successMeanKey,totalHite5xx]
        returnResult = self.getRemoteData( requestKeyDict )
        #取得单机的区间
        sumSuccessLess500 = returnResult[successLessKey1]
        sumSuccessLess1s = returnResult[successLessKey2]
        sumSuccessLess2s = returnResult[successLessKey3]
        sumSuccessLess4s = returnResult[successLessKey4]
        sumSuccessOver4s = returnResult[successLessKey5]
        #取得失败总数
        sumTotal5xx=returnResult[totalHite5xx]
        #取得单机的成功的总的点击次数
        sumSuccessHit = returnResult[successHitsKey1]
        #取得单机的总的点击次数
        sumTotalHitKey = returnResult[totalHitsKey2]
        sumSuccessMeanKey = returnResult[successMeanKey]
        for idcName in self.idcInfo.keys():
            if _ip.find(idcName) >=0:
                idSeek = _ip.find(idcName)+len(idcName)
                idc = _ip[0:idSeek]
                if not self.coreIdc.has_key(idc):
                    self.coreIdc[idc]={}
        if (sumSuccessHit < self.everyM and sumTotalHitKey<self.everyM):
            _status = "OK"
            rate1=0
            rate2=0
            rate3=0
            avgTime=0
            self.logObj.info("ip:%s code:%d msg:key(total success hits)value(%s) key(total hits) value(%s)"%(_ip, globalVariable.returnCode[_status],sumSuccessHit,sumTotalHitKey))
            #取remote的数值来决定"
        else:
            if ( sumTotalHitKey < 1 or  (sumTotalHitKey-sumSuccessHit ) < 1 ):
                rate1 = 0
            else:
                rate1=sumTotal5xx/sumTotalHitKey
            if ( sumSuccessHit < 1 or (sumSuccessHit-sumSuccessLess500-sumSuccessLess1s) < 1 ):
                rate2 = 0
            else:
                rate2=(sumSuccessHit-sumSuccessLess500-sumSuccessLess1s)/sumSuccessHit
            if ( sumSuccessHit < 1 or (sumSuccessHit-sumSuccessLess500-sumSuccessLess1s-sumSuccessLess2s) < 1 ):
                rate3 = 0
            else:
                rate3=(sumSuccessHit-sumSuccessLess500-sumSuccessLess1s-sumSuccessLess2s)/sumSuccessHit
            if ( rate1 > self.alertFailedRate or rate2 > self.warningTimeOut or rate3 > self.errorTimeOut ):
                _status = "CRITICAL"
            else:
                _status = "OK"
            if sumTotalHitKey==0:
                avgTime = 0
            else:
                avgTime = sumSuccessMeanKey/sumTotalHitKey
        retMsgIP = "HTTP_CHECK %s:5xx( (5xx %d/total:%d ) = %.2f%%;upper1s( (2xx:%d - <500:%d - <1s:%d)/2xx:%d) = %.2f%%;upper2s( (2xx:%d - <500:%d - <1s:%d - <2s:%d)/total:%d) = %.2f%% |avgTime=%.2fs"%(_status,sumTotal5xx,sumTotalHitKey,rate1*100,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessHit,rate2*100,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessLess2s,sumSuccessHit,rate3*100,avgTime)
        self.logObj.info("ip:%s code:%d msg:%s,sumTotalHitKey=%.2f,sumSuccessHit=%.2f,sumSuccessLess500=%.2f,sumSuccessLess1s=%.2f,sumSuccessLess2s=%.2f,sumSuccessLess4s=%.2f,sumSuccessOver4s=%.2f)"%(_ip, globalVariable.returnCode[_status], retMsgIP,sumTotalHitKey,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessLess2s,sumSuccessLess4s,sumSuccessOver4s ))
        #若只发送warning,critical并且status为ok的话，则返回None
        if ( self.conf['config']['alertflag'] == 1 and _status == "ok" ):
            return None
        else:
            return {"retCode":globalVariable.returnCode[_status],"retMsgIP":retMsgIP}
    #合并idc的监控指标
    def mergeIDCData(self,idcName):
        retMsgIDC = ''
        #print idcName
        sumSuccessHit=0
        sumSuccessLess500=0
        sumSuccessLess1s=0
        sumSuccessLess2s=0
        sumSuccessLess4s=0
        sumSuccessOver4s=0
        sumTotalHitKey=0
        sumSuccessMeanKey=0
        sumTotal5xx=0
        #IDC成功数key
        successHitsKey1 = "%s.total_less.hits"%( idcName)
        #IDC总数key
        totalHitsKey2 = "%s.total_hits.hits"%( idcName)
        #返回给nagios的缺省值
        _status = "OK"
        #IDC响应时间区间key
        successLessKey1 = "%s.http_2xx.less_500ms"%( idcName)
        successLessKey2 = "%s.http_2xx.less_1s"%( idcName)
        successLessKey3 = "%s.http_2xx.less_2s"%( idcName)
        successLessKey4 = "%s.http_2xx.less_4s"%( idcName)
        successLessKey5 = "%s.http_2xx.over_4s"%( idcName)
        successMeanKey = "%s.http_2xx.mean"%(idcName)
        #失败总数
        total5xxKey = "%s.http_5xx.hits"%(idcName)
        #向远端发送请求的key列表
        requestKeyDict= [successHitsKey1,totalHitsKey2,successLessKey1,successLessKey2,successLessKey3,successLessKey4,successLessKey5,successMeanKey,total5xxKey]
        returnResult = self.getRemoteData( requestKeyDict )
        #取得IDC的区间时间
        #print returnResult[successLessKey1]
        sumSuccessLess500 = returnResult[successLessKey1]
        sumSuccessLess1s = returnResult[successLessKey2]
        sumSuccessLess2s = returnResult[successLessKey3]
        sumSuccessLess4s = returnResult[successLessKey4]
        sumSuccessOver4s = returnResult[successLessKey5]
        #取得单节口的成功的总的点击次数 相加
        sumSuccessHit = returnResult[successHitsKey1]
        #取得单节口的总的点击次数
        sumTotalHitKey = returnResult[totalHitsKey2]
        sumSuccessMeanKey = returnResult[successMeanKey]
        sumTotal5xx=returnResult[total5xxKey]
        if (sumSuccessHit < self.everyM and sumTotalHitKey<self.everyM):
            _status = "OK"
            rate1=0
            rate2=0
            rate3=0
            avgTime=0
            self.logObj.info("IDC:%s code:%d msg:key(total success hits)value(%s) key(total hits) value(%s)"%(idcName, globalVariable.returnCode[_status],sumSuccessHit,sumTotalHitKey))
            #取remote的数值来决定"
        else:
            if ( sumTotalHitKey < 1 or  (sumTotalHitKey-sumSuccessHit ) < 1 ):
                rate1 = 0
            else:
                rate1=sumTotal5xx/sumTotalHitKey
            if ( sumSuccessHit < 1 or (sumSuccessHit-sumSuccessLess500-sumSuccessLess1s) < 1 ):
                rate2 = 0
            else:
                rate2=(sumSuccessHit-sumSuccessLess500-sumSuccessLess1s)/sumSuccessHit
            if ( sumSuccessHit < 1 or (sumSuccessHit-sumSuccessLess500-sumSuccessLess1s-sumSuccessLess2s) < 1 ):
                rate3 = 0
            else:
                rate3=(sumSuccessHit-sumSuccessLess500-sumSuccessLess1s-sumSuccessLess2s)/sumSuccessHit
            if ( rate1 > self.alertFailedRate or rate2 > self.warningTimeOut or rate3 > self.errorTimeOut ):
                _status = "CRITICAL"
            else:
                _status = "OK"
            if sumTotalHitKey==0:
                avgTime = 0
            else:
                avgTime = sumSuccessMeanKey
        retMsgIDC = "HTTP_CHECK  IDC %s:5xx( (5xx %d/total:%d ) = %.2f%%;upper1s( (2xx:%d - <500:%d - <1s:%d)/2xx:%d) = %.2f%%;upper2s( (2xx:%d - <500:%d - <1s:%d - <2s:%d)/total:%d) = %.2f%% |avgTime=%.2fs"%(_status,sumTotal5xx,sumTotalHitKey,rate1*100,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessHit,rate2*100,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessLess2s,sumSuccessHit,rate3*100,avgTime)
        self.logObj.info("IDC:%s code:%d msg:%s,sumTotalHitKey=%.2f,sumSuccessHit=%.2f,sumSuccessLess500=%.2f,sumSuccessLess1s=%.2f,sumSuccessLess2s=%.2f,sumSuccessLess4s=%.2f,sumSuccessOver4s=%.2f)"%(idcName, globalVariable.returnCode[_status], retMsgIDC,sumTotalHitKey,sumSuccessHit,sumSuccessLess500,sumSuccessLess1s,sumSuccessLess2s,sumSuccessLess4s,sumSuccessOver4s ))
        #若只发送warning,critical并且status为ok的话，则返回None
        if ( self.conf['config']['alertflag'] == 1 and _status == "ok" ):
            return None
        else:
            return {"retCode":globalVariable.returnCode[_status],"retMsgIDC":retMsgIDC}

    def check( self, _ip, _interface ):
        #单机单接口成功数key
        successHitsKey1 = "%s.total_less.%s.hits"%( _ip, _interface)
        #单机单接口总数key
        totalHitsKey2 = "%s.total_hits.%s.hits"%( _ip, _interface)
        #返回给nagios的缺省值
        _status = "OK"
        #单机响应时间区间key
        successLessKey1 = "%s.http_2xx.%s.less_500ms"%( _ip, _interface)
        successLessKey2 = "%s.http_2xx.%s.less_1s"%( _ip, _interface)
        successLessKey3 = "%s.http_2xx.%s.less_2s"%( _ip, _interface)
        successLessKey4 = "%s.http_2xx.%s.less_4s"%( _ip, _interface)
        successLessKey5 = "%s.http_2xx.%s.over_4s"%( _ip, _interface)
        total5xxKey     = "%s.http_5xx.%s.hits"%( _ip, _interface)
        #单机平均响应时间key
        successMeanKey = "%s.http_2xx.%s.mean"%(_ip, _interface)

        #向远端发送请求的key列表
        requestKeyDict= [successHitsKey1,totalHitsKey2,successLessKey1,successLessKey2,successLessKey3,successLessKey4,successLessKey5,successMeanKey,total5xxKey]
        returnResult = self.getRemoteData( requestKeyDict )

        #返回的数据结果：key:value|key:value
        if (returnResult[successHitsKey1] < self.everyM and returnResult[totalHitsKey2] < self.everyM):
            _status = "OK"
            rate1=0
            rate2=0
            rate3=0
            avgTime=returnResult[successMeanKey]
            self.logObj.info("ip:%s-api:%s code:%d msg:key(%s)value(%s) key(%s) value(%s)"%(_ip, _interface, globalVariable.returnCode[_status],successHitsKey1,returnResult[successHitsKey1],totalHitsKey2,returnResult[totalHitsKey2]))
            #取remote的数值来决定"
        else:
            if ( returnResult[totalHitsKey2] < 1 or  (returnResult[totalHitsKey2]-returnResult[successHitsKey1] ) < 1 ):
                rate1 = 0
            else:
                rate1=returnResult[total5xxKey]/returnResult[totalHitsKey2]
            if ( returnResult[successHitsKey1] < 1 or (returnResult[successHitsKey1]-returnResult[successLessKey1]-returnResult[successLessKey2]) < 1 ):
                rate2 = 0
            else:
                rate2=(returnResult[successHitsKey1]-returnResult[successLessKey1]-returnResult[successLessKey2])/returnResult[successHitsKey1]
            if(returnResult[successHitsKey1] < 1 or (returnResult[successHitsKey1]-returnResult[successLessKey1]-returnResult[successLessKey2]-returnResult[successLessKey3])<1):
                rate3=0
            else:
                rate3=(returnResult[successHitsKey1]-returnResult[successLessKey1]-returnResult[successLessKey2]-returnResult[successLessKey3])/returnResult[successHitsKey1]
            if ( rate1 > self.alertFailedRate or rate2 > self.warningTimeOut or rate3 > self.errorTimeOut ):
                _status = "CRITICAL"
            else:
                _status = "OK"
            avgTime=returnResult[successMeanKey]
        #print returnResult[total5xxKey]
        retMsg = "HTTP_CHECK %s:5xx %d/total:%d ) = %.2f%%;upper1s( (2xx:%d - <500:%d - <1s:%d)/2xx:%d) = %.2f%%;upper2s( (2xx:%d - <500:%d - <1s:%d - <2s:%d)/total:%d) = %.2f%% |avgTime=%.2fs"%(_status,returnResult[total5xxKey],returnResult[totalHitsKey2],rate1*100,returnResult[successHitsKey1],returnResult[successLessKey1],returnResult[successLessKey2],returnResult[successHitsKey1],rate2*100,returnResult[successHitsKey1],returnResult[successLessKey1],returnResult[successLessKey2],returnResult[successLessKey3],returnResult[successHitsKey1],rate3*100,avgTime)
        self.logObj.info("ip:%s-api:%s code:%d msg:%s)"%(_ip, _interface, globalVariable.returnCode[_status], retMsg ))
        #若只发送warning,critical并且status为ok的话，则返回None
        if ( self.conf['config']['alertflag'] == 1 and _status == "ok" ):
            return None
        else:
            return {"retCode":globalVariable.returnCode[_status],"retMsg":retMsg}
"""
    checkResult=check(args.ip, args.api, args.alertFailedRate, args.warningtimeout, args.errortimeout,args.flag)
    print checkResult["retMsg"]
    sys.exit(checkResult["retCode"] )
"""
