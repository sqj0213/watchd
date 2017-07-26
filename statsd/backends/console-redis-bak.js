/*jshint node:true, laxcomma:true */

var util = require('util');
var redis = require('redis');
var crc32Obj = require('buffer-crc32');
//var map = require('../lib/map.js');
var debug;
//用来存储ip与api列表的redis,只能用一台来存储
var redisMaster;
var redisCluster;
var redisExpireTime;

function Map() {
    this.elements = new Array();
 
    //获取MAP元素个数
    this.size = function() {
        return this.elements.length;
    }
 
    //判断MAP是否为空
    this.isEmpty = function() {
        return (this.elements.length < 1);
    }
 
    //删除MAP所有元素
    this.clear = function() {
        this.elements = new Array();
    }
 
    //向MAP中增加元素（key, value) 
    this.put = function(_key, _value) {
        this.elements.push( {
            key : _key,
            value : _value
        });
    }
 
    //删除指定KEY的元素，成功返回True，失败返回False
    this.remove = function(_key) {
        var bln = false;
        try {
            for (i = 0; i < this.elements.length; i++) {
                if (this.elements[i].key == _key) {
                    this.elements.splice(i, 1);
                    return true;
                }
            }
        } catch (e) {
            bln = false;
        }
        return bln;
    }
 
    //获取指定KEY的元素值VALUE，失败返回NULL
    this.get = function(_key) {
        try {
            for (i = 0; i < this.elements.length; i++) {
                if (this.elements[i].key == _key) {
                    return this.elements[i].value;
                }
            }
        } catch (e) {
            return null;
        }
    }

    //更新指定KEY的元素值VALUE，失败返回NULL
    this.update = function(_key, _value) {
        try {
            for (i = 0; i < this.elements.length; i++) {
                if (this.elements[i].key == _key) {
                    this.elements[i].value = _value;
                }
            }
        } catch (e) {
            return null;
        }
    }
 
    //获取指定索引的元素（使用element.key，element.value获取KEY和VALUE），失败返回NULL
    this.element = function(_index) {
        if (_index < 0 || _index >= this.elements.length) {
            return null;
        }
        return this.elements[_index];
    }
 
    //判断MAP中是否含有指定KEY的元素
    this.containsKey = function(_key) {
        var bln = false;
        try {
            for (i = 0; i < this.elements.length; i++) {
                if (this.elements[i].key == _key) {
                    bln = true;
                }
            }
        } catch (e) {
            bln = false;
        }
        return bln;
    }
 
    //判断MAP中是否含有指定VALUE的元素
    this.containsValue = function(_value) {
        var bln = false;
        try {
            for (i = 0; i < this.elements.length; i++) {
                if (this.elements[i].value == _value) {
                    bln = true;
                }
            }
        } catch (e) {
            bln = false;
        }
        return bln;
    }
 
    //获取MAP中所有VALUE的数组（ARRAY）
    this.values = function() {
        var arr = new Array();
        for (i = 0; i < this.elements.length; i++) {
            arr.push(this.elements[i].value);
        }
        return arr;
    }
 
    //获取MAP中所有KEY的数组（ARRAY）
    this.keys = function() {
        var arr = new Array();
        for (i = 0; i < this.elements.length; i++) {
            arr.push(this.elements[i].key);
        }
        return arr;
    }
}


function ConsoleBackend(startupTime, config, emitter){
    var self = this;
    this.lastFlush = startupTime;
    this.lastException = startupTime;
    this.config = config.console || {};

    // attach
    emitter.on('flush', function(timestamp, metrics) { self.flush(timestamp, metrics); });
    emitter.on('status', function(callback) { self.status(callback); });
}

ConsoleBackend.prototype.flush = function(timestamp, metrics)
{
    var keyNumStats = 0;
    var timerNumStats = 0;
    var counters = metrics.counters;
    var timers = metrics.timers;
    var beginTime = getDateTime( new Date());
    var t1 = (new Date).getTime();
    var logStr = beginTime;
    var debugLogStr = "";
    var filterKeyCount=0;
    var filterTimerCount=0;
    var redisClusterLen=0;
    //用来存储ip与api列表的redis对象
    var redisMasterObj;
    //redis集群对象
    var redisClientObjList;

    //单机单接口总量按照状态码聚合计算
    //用来聚合计算openapi.coreapi_yf.byhost.10_75_5_73.total_hits._2_counter_get_count_json.hits
    //用来聚合计算openapi.coreapi_yf.byhost.10_75_24_31.total_less._2_counter_get_count_json.hits
    //用来聚合计算timers.coreapi_yf.byhost.10_75_24_31.http_2xx._2_counter_get_count_json.means
    var ipApiMergeList = new Map();

    //单机维度总量按照状态码聚合计算
    //用来聚合计算openapi.coreapi_yf.byhost.10_75_5_73.(http_4xx|http_5xx|http_2xx|total_hits).hits
    //用来聚合计算openapi.coreapi_yf.byhost.10_75_24_31.((http_2xx.(less_1s|less_500ms|less_2s|less_4s|over_4s))|(total_less.hits))
    //用来聚合计算timers.coreapi_yf.byhost.10_75_24_31.http_2xx.means
    var ipMergeList = new Map();

    //idc维度总量按照状态码聚合计算
    //用来聚合计算openapi.coreapi_yf.(http_4xx|http_5xx|http_2xx|total_hits).hits
    //用来聚合计算openapi.coreapi_yf.(http_2xx.(less_1s|less_500ms|less_2s|less_4s|over_4s))|(total_less.hits))
    //用来聚合计算timers.coreapi_yf.http_2xx.means
    var idcMergeList = new Map();


    function getDateTime(date) {
        var year = date.getFullYear();
        var month = date.getMonth() + 1;
        var day = date.getDate();
        var hh = date.getHours();
        var mm = date.getMinutes();
        var ss = date.getSeconds();
        return year + "-" + month + "-" + day + " " + hh + ":" + mm + ":" + ss;
    }

    function reconnectRedisCluster()
    {
        var retArray= new Array();
        for( var j=0; j < redisCluster.length;j++ )
        {
            retArray[redisClusterLen] = redis.createClient( redisCluster[j]['port'], redisCluster[j]['host'] );
            //填加error事件侦听，后端redis有问题时要捕捉，不然程序会shutdown
            retArray[redisClusterLen].on('error',function(err){console.log(err);});
            redisClusterLen++;
            if ( debug )
                console.log("init i:"+redisClusterLen+" redis("+redisCluster[j]['host']+":"+redisCluster[j]['port']+")!");
        }
        return retArray;
    }

    function redisClose(  )
    {
        if ( debug )
            console.log("begin close redis cluster!");
        for( var i=0; i < redisClientObjList.length;i++ )
        {
            redisClientObjList[i].quit();
        }
        if ( debug )
            console.log("end close redis cluster!");
    }
    function mergeData(){
        
    }
    //通过key截取对应的api ip idc
    function apiIpIdcKeyName(key,type){
        var ipName = "";
        var idcName = "";
        var ipApiTotalHitsName = "";
        var ipApiTotalLessName = "";
        var ipTotalHitsName = "";
        var ipTotalLessName = "";
        var idcTotalHitsName = "";
        var idcTotalLessName = "";

        if(type == "api"){
            return key;
        }
        var strs= new Array();
        strs=key.split(".byhost.");
        //if(strs.length < 2){
        //    console.log("key error :"+key);
        //}
        idcName = strs[0];
        tmp=strs[1].split(".");
        //if(tmp.length < 2){
        //    console.log("key error :"+key);
        //}

        if(type == "ip"){
            ipName = idcName + '.byhost.' + tmp[0] + '.' + tmp[1] + '.' + tmp[3];
            if ( tmp[3] == 'hits') {
                ipApiTotalHitsName = idcName + '.byhost.' + tmp[0] + '.total_hits.' + tmp[2] + '.' + tmp[3];
                ipTotalHitsName = idcName + '.byhost.' + tmp[0] + '.total_hits.' + tmp[3];
            }
            else {
                ipApiTotalLessName = idcName + '.byhost.' + tmp[0] + '.total_less.' + tmp[2] + '.hits';
                ipTotalLessName = idcName + '.byhost.' + tmp[0] + '.total_less.' + 'hits';
            }
            //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits
            //返回如下
            //openapi.blossomin_yf.byhost.10_75_0_53.http_2xx.hits,
            //openapi.blossomin_yf.byhost.10_75_0_53.total_hits._2_remind_set_count_json.hits
            //openapi.blossomin_yf.byhost.10_75_0_53.total_hits.hits
            //""
            //""
            //若传入的key为:openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_500ms
            //返回如下：
            //openapi.blossomin_yf.byhost.10_75_0_53.http_2xx.less_500ms
            //""
            //""
            //openapi.blossomin_yf.byhost.10_75_0_53.total_less._2_counter_get_count_json.hits
            //openapi.blossomin_yf.byhost.10_75_0_53.total_less.hits
            return [ipName,ipApiTotalHitsName,ipTotalHitsName,ipApiTotalLessName,ipTotalLessName]
        }else if(type == "idc"){
            //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits
            //返回如下:
            //openapi.blossomin_yf.http_2xx.hits
            //openapi.blossomin_yf.total_hits.hits
            //""
            //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.less_500ms
            //返回如下:
            //openapi.blossomin_yf.http_2xx.less_500ms
            //""
            //openapi.blossomin_yf.total_less.hits
            var idcNameTmp = idcName + '.' + tmp[1] + '.' + tmp[3];
            if ( tmp[3] == 'hits')
                idcTotalHitsName = idcName + '.total_hits.' + tmp[3];
            else
                idcTotalLessName = idcName + '.total_less.' + 'hits';
            return [idcNameTmp,idcTotalHitsName,idcTotalLessName];
        }

    }
    
    //此方法不通用，可以再抽象，考虑正则来优化
    function getHashIndex( srcKey )
    {
        var startPos=8;
        var count = 0;
        var tmpVal = 0;
        var host='';
        for ( var i = 0; i < 3; i++)
        {
            if ( ( tmpVal = srcKey.indexOf('.', startPos + 1 ) ) !== -1 )
            {
                startPos = tmpVal + 1;
            }
        }
        host = srcKey.substr(0, startPos - 1 );
        return crc32Obj.unsigned(host)%redisClusterLen;
    }

    //srcKey为ip字符串，直接返回编码HashIndex
    function getCrc320bjHashIndex(srcKey){
        return crc32Obj.unsigned(srcKey)%redisClusterLen;
    }

    if ( debug )
        console.log("begin init redis cluster!");
    redisMasterObj = redis.createClient(redisMaster['port'],redisMaster['host']);
    //清空apilist,避免重复累加
    
   
    redisClientObjList=reconnectRedisCluster();
    if ( debug )
        console.log("end init redis cluster!");

    // Sanitize key for graphite if not done globally
    function sk(srcStr)
    {
        if (    srcStr.lastIndexOf('.hits') !== -1
                || srcStr.lastIndexOf('500ms') !== -1
                || srcStr.lastIndexOf('ss_1s') !== -1
                || srcStr.lastIndexOf('ss_2s') !== -1
                || srcStr.lastIndexOf('ss_4s') !== -1
                || srcStr.lastIndexOf('er_4s') !== -1
                || srcStr.lastIndexOf('.mean') !== -1 ) 
        {
            if ( ( /[\d]{9,}/.test(srcStr )) ||  srcStr.lastIndexOf('.None.') !== -1 || (srcStr.lastIndexOf('byhost') == -1) )
                return '';
            else
                return srcStr;
        }
        else
            return '';
    };

    if ( debug )
        debugLogStr = "filter count key log:";
    
    var delkey_flag = 0 
    for (var key in counters)
    {
        //不包含byhost的key要全部过滤掉，ip与idc的聚合运算，通过statsd来计算
        var keyName = sk(key);
        if (keyName.length == 0)
        {
            if ( debug )
                if ( filterKeyCount  == 0 )
                    debugLogStr = debugLogStr  + "\t"+ key + ":"+ counters[key];
                else
                    debugLogStr = debugLogStr +  "|"+ key + ":"+ counters[key];
            filterKeyCount += 1;
            continue;
        }
        //单机单接口的数据要过滤，不做计算
        //total的值需要聚合运算，不使用发过来的值，只用来获取上线的ip与ip下的所有api
        if ( key.indexOf( "byhost" ) !== -1 && ( key.indexOf( "total" ) !== -1 ) ) {
            if(delkey_flag == 0){
                redisMasterObj.del('apiKeyList');
            }
            delkey_flag = delkey_flag + 1;
            //nagios监控项
            redisMasterObj.sadd("apiKeyListNagios", keyName);
            redisMasterObj.sadd("apiKeyList", keyName);
            continue;
        }

        var value = counters[key];
        //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits
        //返回如下
        //openapi.blossomin_yf.byhost.10_75_0_53.http_2xx.hits,
        //openapi.blossomin_yf.byhost.10_75_0_53.total_hits._2_remind_set_count_json.hits
        //openapi.blossomin_yf.byhost.10_75_0_53.total_hits.hits
        //""
        //""
        //若传入的key为:openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_counter_get_count_json.less_500ms
        //返回如下：
        //openapi.blossomin_yf.byhost.10_75_0_53.http_2xx.less_500ms
        //""
        //""
        //openapi.blossomin_yf.byhost.10_75_0_53.total_less._2_counter_get_count_json.hits
        //openapi.blossomin_yf.byhost.10_75_0_53.total_less.hits
        var ipApiKeyNameList = apiIpIdcKeyName(keyName,'ip');
        var ipName = ipApiKeyNameList[0];
        var ipApiTotalHitsKeyName = ipApiKeyNameList[1];
        var ipTotalHitsKeyName = ipApiKeyNameList[2];
        var ipApiTotalLessKeyName = ipApiKeyNameList[3];
        var ipTotalLessKeyName = ipApiKeyNameList[4];

        //ipapi部分的hits聚合,else部分为less聚合
        if ( ipApiTotalHitsKeyName !== "" )
        {
            //ipapi部分的聚合，聚合此键openapi.blossomin_yf.byhost.10_75_0_53.total_hits._2_remind_set_count_json.hits
            if ( ipApiMergeList.containsKey( ipApiTotalHitsKeyName ) ) {
                total = ipApiMergeList.get( ipApiTotalHitsKeyName ) + value;
                ipApiMergeList.update( ipApiTotalHitsKeyName, total );
            }
            else
                ipApiMergeList.put( ipApiTotalHitsKeyName, value );

            //ip部分的聚合，聚合此键openapi.blossomin_yf.byhost.10_75_0_53.total_hits.hits
            if ( ipMergeList.containsKey( ipTotalHitsKeyName ) ) {
                total = ipMergeList.get( ipTotalHitsKeyName ) + value;
                ipMergeList.update( ipTotalHitsKeyName, total );
            }
            else
                ipMergeList.put( ipTotalHitsKeyName, value );
        }
        //ipapi部分的less聚合
        else
        {
            //ipapi部分聚合，聚合此键openapi.blossomin_yf.byhost.10_75_0_53.total_less._2_counter_get_count_json.hits
            if ( ipApiMergeList.containsKey( ipApiTotalLessKeyName ) )
            {
                total = ipApiMergeList.get( ipApiTotalLessKeyName ) + value;
                ipApiMergeList.update( ipApiTotalLessKeyName, total );
            }
            else
                ipApiMergeList.put( ipApiTotalLessKeyName, value );
            //ip部分聚合，聚合此键:openapi.blossomin_yf.byhost.10_75_0_53.total_less.hits
            if ( ipMergeList.containsKey( ipTotalLessKeyName ) )
            {
                total = ipMergeList.get( ipTotalLessKeyName ) + value;
                ipMergeList.update( ipTotalLessKeyName, total );
            }
            else
                ipMergeList.put( ipTotalLessKeyName, value );
        }
        //聚合ip
        if( ipMergeList.containsKey(ipName) ){
            total = ipMergeList.get(ipName) + value;
            ipMergeList.update(ipName, total);
        }else{
            ipMergeList.put(ipName, value);
        }
        if ( debug )
            console.log('key:'+keyName+'***start merge dic');



        //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.hits
        //返回如下:
        //openapi.blossomin_yf.http_2xx.hits
        //openapi.blossomin_yf.total_hits.hits
        //""
        //若传入的key为：openapi.blossomin_yf.byhost.10_75_0_53.http_2xx._2_remind_set_count_json.less_500ms
        //返回如下:
        //openapi.blossomin_yf.http_2xx.less_500ms
        //""
        //openapi.blossomin_yf.total_less.hits
        var idcNameKeyNameList = apiIpIdcKeyName(keyName,'idc');
        var idcName = idcNameKeyNameList[0];
        var idcTotalHitsKeyName = idcNameKeyNameList[1];
        var idcTotalLessKeyName = idcNameKeyNameList[2];
        if ( debug )
            console.log('key:'+keyName+'***start merge ip');

        //按照idc聚合hits,else部分聚合less
        if ( idcTotalHitsKeyName !== "" )
        {
            //聚合此key：openapi.blossomin_yf.total_hits.hits
            if ( idcMergeList.containsKey( idcTotalHitsKeyName ) )
            {
                total = idcMergeList.get( idcTotalHitsKeyName ) + value;
                idcMergeList.update( idcTotalHitsKeyName, total );
            }
            else
                idcMergeList.put( idcTotalHitsKeyName, value );
        }
        //按照idc聚合less
        else
        {
            //聚合此key：openapi.blossomin_yf.total_less.hits
            if ( idcMergeList.containsKey( idcTotalLessKeyName ) ) {
                total = idcMergeList.get(idcTotalLessKeyName) + value;
                idcMergeList.update(idcTotalLessKeyName, total);
            }
            else
                idcMergeList.put( idcTotalLessKeyName, value );

        }

        //聚合idc
        if( idcMergeList.containsKey(idcName) ){
            total = idcMergeList.get(idcName) + value;
            idcMergeList.update(idcName, total);
        }else{
            idcMergeList.put(idcName, value);
        }
        if ( debug )
            console.log('key:'+keyName+'***finish merge ip and dic');


        //stats明细结果直接入redis
        var hashIndex = getHashIndex( keyName );
        if ( debug )
            console.log('key:'+keyName+' value:'+value+' host:'+redisCluster[hashIndex]['host']+':'+redisCluster[hashIndex]['port']);
        redisClientObjList[hashIndex].set( keyName, value );
        redisClientObjList[hashIndex].expire( keyName, redisExpireTime );

        keyNumStats += 1;
    }


    //ipApiMergeList 写redis
    for( var i=0; i<ipApiMergeList.size();i++){ //item in ipMergeList.elements ){
        var item = ipApiMergeList.element(i);
        var ipName_temp = item.key;
        //console.log(ipName_temp)
        var ip_value = item.value;
        var hashIndex = getHashIndex( ipName_temp );
        if ( debug )
            console.log('ipApiMergeList***'+'key:'+ipName_temp+' value:'+ip_value+' host:'+redisCluster[hashIndex]['host']+':'+redisCluster[hashIndex]['port']);
        redisClientObjList[hashIndex].set( ipName_temp, ip_value );
        redisClientObjList[hashIndex].expire( ipName_temp, redisExpireTime );
        //redisClientObjList[hashIndex].sadd( "ipApiKeyList", ipName_temp );
        if ( debug )
            console.log('ipApiMergeList***'+'key:'+ipName_temp+' value:'+ip_value+' finish save to redis');
    }

    //ipMergeList 写redis
    for( var i=0; i<ipMergeList.size();i++){ //item in ipMergeList.elements ){
	    var item = ipMergeList.element(i);
        var ipName_temp = item.key;
        //console.log(ipName_temp)
        var ip_value = item.value;
        var hashIndex = getCrc320bjHashIndex( ipName_temp );
        if ( debug )
            console.log('IPMerge***'+'key:'+ipName_temp+' value:'+ip_value+' host:'+redisCluster[hashIndex]['host']+':'+redisCluster[hashIndex]['port']);
        redisClientObjList[hashIndex].set( ipName_temp, ip_value );
        redisClientObjList[hashIndex].expire( ipName_temp, redisExpireTime );
        if(i==0){
            redisMasterObj.del('ipKeyList');
        }
        redisMasterObj.sadd( "ipKeyList", ipName_temp );
        if ( debug )
            console.log('IPMerge***'+'key:'+ipName_temp+' value:'+ip_value+' finish save to redis');
    }


    //idcMergeList 写redis
    for( var i=0; i<idcMergeList.size();i++){
        var temp = idcMergeList.element(i);
        var idcName_temp = temp.key;
        var idc_value = temp.value;
        var hashIndex = getCrc320bjHashIndex( idcName_temp );
        if ( debug )
            console.log('IDCMerge***'+'key:'+idcName_temp+' value:'+idc_value+' host:'+redisCluster[hashIndex]['host']+':'+redisCluster[hashIndex]['port']);
        redisClientObjList[hashIndex].set( idcName_temp, idc_value );
        redisClientObjList[hashIndex].expire( idcName_temp, redisExpireTime );
        if(i==0){
            redisMasterObj.del('idcKeyList');
        }
        redisMasterObj.sadd( "idcKeyList", idcName_temp );
        if ( debug )
            console.log('IDCMerge***'+'key:'+idcName_temp+' value:'+idc_value+' finish save to redis');
    }


    var t2 = (new Date).getTime();
    logStr = logStr + "\tt2-t1="+(t2-t1)+"\tkeyNumstats="+keyNumStats+":filterKeyCount="+filterKeyCount;
    if ( debug )
        debugLogStr = debugLogStr+"\tfilter timer key log:";
    
    for (key in timers)
    {
        var keyName = sk(key);
        if ( keyName.length == 0 )
        {
            if ( debug )
                if ( filterTimerCount  == 0 )
                    debugLogStr = debugLogStr + "\t"+ key + ":"+ counters[key];
                else
                    debugLogStr = debugLogStr + "|"+ key + ":"+ counters[key];
            filterTimerCount += 1;
            continue;
        }
        var hashIndex = getHashIndex( keyName );
        if ( debug )
            console.log('key:'+keyName+' value:'+timers[keyName]+ 'host:'+redisCluster[hashIndex]['host']+':'+redisCluster[hashIndex]['port']);
        redisClientObjList[hashIndex].set( keyName, timers[keyName]);
        redisClientObjList[hashIndex].sadd( "apiTimerList", keyName );
        redisClientObjList[hashIndex].expire( keyName, redisExpireTime );
        timerNumStats += 1;
    }
    var t3 = (new Date).getTime();
    logStr = logStr + "\tt3-t2="+(t3-t2)+"\ttimerNumstats="+timerNumStats+":filterTimerCount="+filterTimerCount;
    var queueNodeData=JSON.stringify(new Array((new Date).getTime(),keyNumStats,timerNumStats));
    //合适时机打开此处日志
    //if ( debug )
    //    logStr = logStr + "\t" + debugLogStr;
    console.log( logStr );
    if ( keyNumStats > 0 || timerNumStats > 0 )
    {
        redisMasterObj.rpush('alertQueue', queueNodeData);
    }
    redisMasterObj.quit();
    redisClose(redisClientObjList);
};

ConsoleBackend.prototype.status = function(write) {
  ['lastFlush', 'lastException'].forEach(function(key) {
    write(null, 'console', key, this[key]);
  }, this);
};

exports.init = function(startupTime, config, events) {
    var instance = new ConsoleBackend(startupTime, config, events);
    debug = config.debug;
    redisCluster=config.redis;
    redisMaster = config.redisCenter;
    redisExpireTime=config.redisExpireTime;
    return true;
};
