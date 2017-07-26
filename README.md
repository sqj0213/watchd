系统结构：

nagios-server:负责告警配置，在异常情况下主动检测接口是否正常，并发送邮件

nsca：nagios-server启用被动监控模式时，需要此组件支持主动向nagios-server发送监控结果数据

statsd-monitor(60秒):

        负责60秒聚合所有监控key
        
        定时写入redis-server
        
        写入完成后填加任务队列信息
        
        只填加含有total与byhost关键字的接口到redis，此种关键字包含机房信息，ip，接口,供watchd进程读取
        
redis-server:负责存储statsd-monitor处理完的60秒的key信息与任务信息，供watchd进程读取

watchd:

    1.以阻塞方式从redis-server读取任务信息，有任务信息时，按照业务要求，读取所有的key
    
    2.组织告警数据，以nsca方式发送告警数据到nagios
    
    3.读取所有的key时，解析所有的ip地址与ip地址所对应的api,写入redis，每5分钟reload一次ip与api数据
    
    4.取出任务信息后，通过遍历ip与ip所对应的api，拼写监控项，并获取数据，组织告警数据
    
    httpCheck线程
    
        1.主线程
        
        2.读取任务
        
        3.根据业务需求组织告警数据
        
        4.以nsca方式发送告警数据到nagios
        
    reloadHostApiList线程
    
1.定时读取ip与api数据共httpCheck线程使用
