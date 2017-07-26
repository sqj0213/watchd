#!/bin/env python
#coding=utf8
import pdb
import threading, time, copy
from lib import include as globalVariable

class reloadHostApiList():

    logObj=None
    redisObj=None
    conf=None
    intervalSecond = 300
    stopFlag=False

    def __init__(self, _logObj=None, _redisObj=None, _conf=None):
        self.logObj = _logObj
        self.redisObj = _redisObj
        self.conf = _conf
        self.intervalSecond = int(_conf['timer']['reloadinterval'])

    def start(self):
        self.logObj.info("reloadHostApiList is started!")
        if self.conf['flag']['stopflag'] == True:
            self.logObj.info("reloadHostApiList is stoped!")
        else:
            hostApiList = list(self.redisObj.smembers( self.conf['redis']['countkeylistname']))
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
            self.logObj.info("reloadHostApiList is finish!")
