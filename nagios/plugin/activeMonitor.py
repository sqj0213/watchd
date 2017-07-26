#!/bine/env python
#coding=utf8
__author__ = 'wangkai'
import pdb
from lib import common
from lib import reloadHostApiList
from check import check
import logging as logObj
from lib import include as globalVariable
import argparse,sys,ConfigParser,redis,threading,signal,time

defaultConfigFilePath='/usr/lib64/nagios/plugins/watchd/nagios/plugin/conf/conf.ini'
#defaultConfigFilePath='./conf/conf.ini'
#获取命令行输入：config路径，ip，接口api
def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default=defaultConfigFilePath, help="please input config file path!" )
    parser.add_argument("--key", type=str, help="please input key" )
    parser.add_argument("--type", type=str, help="please input type" )
    args = parser.parse_args()
    return args

#配置文件初始化
def init_config(args):
    cf = ConfigParser.ConfigParser()
    cf.read( args.config )
    conf = common.convertListToDict( cf )
    return conf

#日志初始化
def init_log(conf):
    logObj.basicConfig(filename=conf[ 'log' ][ 'access' ],filemode='a+',level=logObj.INFO, format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s %(filename)s %(module)s %(lineno)d', datefmt='%Y-%m-%d %H:%M:%S' )
    #debug开关，需要更多日志时改为True
    #pdb.set_trace()
    if globalVariable.debugflag == False:
        logObj.disable(logObj.info)
    return logObj

#redis初始化
def init_redis(conf):
    redisObj = redis.Redis(conf['redis']['host'],int(conf['redis']['port']))
    return redisObj
    #redisObj.get("openapi.blossomin_yf.byhost.10_75_0_53.http2xx._2_remind_set_count_json.hits")


if __name__ == "__main__":
    #time.sleep(50);
    #print "test debug"
    #sys.exit(1)
    args = init_parser()
    config = init_config(args)
    logObj = init_log(config)
    redisObj = init_redis(config)
    #初始化主动监控
    checkObj = check.check( logObj, redisObj, config, args.key, args.type)
    #start main thread
    logObj.info("check ip and api from redis is started!")
    checkObj.start()




