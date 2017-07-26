#!/bine/env python
#coding=utf8
__author__ = 'sunshare'
import argparse,sys,ConfigParser,redis,threading,signal,time
import logging as logObj
from baseLib import common
from inc import include as globalVariable
from inc import httpCheck as httpCheck
from inc import reloadHostApiList as reloadHostApiList
redisObj=None
conf=None
defaultConfigFilePath='/usr/local/monitor/watchd/conf/conf.ini'
#windows下运行修改
#defaultConfigFilePath='conf/conf.ini'
parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default=defaultConfigFilePath, help="please input config file path!" )
args = parser.parse_args()

#init configure
cf = ConfigParser.ConfigParser()
cf.read( args.config )
conf = common.convertListToDict( cf )

#init redis99
redisObj = redis.Redis(conf["queue"]["host"],int(conf["queue"]["port"]))

#init logObj
logObj.basicConfig(filename=conf[ 'log' ][ 'access' ],filemode='a+',level=logObj.INFO, format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s %(filename)s %(module)s %(lineno)d', datefmt='%Y-%m-%d %H:%M:%S' )
if globalVariable.debugFlag == False:
	logObj.disable(logObj.info)

#init reload thread
reloadHostApiListObj = reloadHostApiList.reloadHostApiList( logObj, redisObj, conf )
reloadHostApiListObj.setDaemon(True)
#start all thread
reloadHostApiListObj.start()

#侦听信号根据线程状态组织退出逻辑
def signal_handler(num, stack):
    logObj.info("Received signal %d in %s" % (num, threading.currentThread()))
    globalVariable.stopFlag = True
    while True:
        if ( httpCheckObj.stopFlag == True and reloadHostApiListObj.stopFlag == True ):
            logObj.info("reloadHostApiList thread is stop!")
            logObj.info("httpCheck thread is stop!")
        time.sleep(1)
    logObj.info("watchd main thread is stop!")
    sys.exit()
#windows 修改
signal.signal(signal.SIGUSR1, signal_handler)

#init httpCheck main thread
httpCheckObj = httpCheck.httpCheck( logObj, redisObj, conf )
#start main thread
logObj.info("watchd main thread is started!")
httpCheckObj.run()
