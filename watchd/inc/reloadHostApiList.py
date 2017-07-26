#!/bin/env python
#coding=utf8
import threading, time, copy
from inc import include as globalVariable

class reloadHostApiList( threading.Thread ):
    logObj=None
    redisObj=None
    conf=None
    intervalSecond = 1
    stopFlag=False
    def __init__(self, _logObj=None, _redisObj=None, _conf=None):
        self.logObj = _logObj
        self.redisObj = _redisObj
        self.conf = _conf
        self.intervalSecond = int(_conf['timer']['reloadinterval'])
        threading.Thread.__init__( self )

    def run(self):
        threadname = threading.currentThread().getName()
        self.logObj.info("reloadHostApiList (%s ) thread started!"%(threadname))
        while True:
            if globalVariable.stopFlag == True:
                self.logObj.info("reloadHostApiList (%s ) thread stoped!"%(threadname))
                break
            hostApiList = list(self.redisObj.smembers( self.conf['queue']['countkeylistname']))
            hostApiListPro = list(self.redisObj.smembers( self.conf['queue']['countkeylistnamepro']))
            hostApiList = hostApiList+hostApiListPro
            ipList=set()
            ipApiList={}
            self.stopFlag = False
            for i in range(len(hostApiList)):
                tmpVal = hostApiList[i].split(".total.")
                if len(tmpVal) < 2:
                    self.logObj.info("read apiKeyList is invalid!apiKeyList value(%s)"%(hostApiList[i]))
                    continue
                ip=tmpVal[0]
                api=tmpVal[1].split(".")[0]
                if ip in ipList:
                    pass
                else:
                    ipList.add(ip)
                    ipApiList[ip]=set()

                if api in ipApiList[ip]:
                    pass
                else:
                    ipApiList[ip].add(api)
            globalVariable.ipList = copy.deepcopy( ipList )
            globalVariable.ipApiList = copy.deepcopy( ipApiList )
            self.logObj.info("reloadHostApiList (%s ) timer sleep(%s)!"%(threadname,self.intervalSecond))
            stopFlag = True
            time.sleep( self.intervalSecond)
