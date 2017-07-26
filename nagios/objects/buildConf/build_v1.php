<?php $hostMonitorTmpl="define servicegroup{
servicegroup_name _HOSTNAME_
members _MEMBERS_
}
";
$membersTmpl="localhost,_API_";

	$redisObj=new Redis();
	$redisObj->connect("10.13.80.58",6379);
	$ipApiList = $redisObj->smembers("apiKeyList");

	$cmdFileTmplBody = file('/etc/nagios/objects/buildConf/platform-monitor-tmpl.cfg');
	$cmdIDCFileTmplBody = file('/etc/nagios/objects/buildConf/platform-monitor-idc-tmpl.cfg');
	$cmdIPFileTmplBody = file('/etc/nagios/objects/buildConf/platform-monitor-ip-tmpl.cfg');
	$destFilePathService = "/etc/nagios/objects/buildConf/platform-monitor.cfg";
	$destFilePathServiceIP = "/etc/nagios/objects/buildConf/platform-monitor-ip.cfg";
	$destFilePathServiceIDC = "/etc/nagios/objects/buildConf/platform-monitor-idc.cfg";
	$destFilePathHostGroupHost = "/etc/nagios/objects/buildConf/platform-monitor-host-group.cfg";
	$destFilePathHostGroupIDC = "/etc/nagios/objects/buildConf/platform-monitor-idc-group.cfg";
	system("/bin/rm -f ".$destFilePathService);
	system("/bin/rm -f ".$destFilePathServiceIP);
	system("/bin/rm -f ".$destFilePathServiceIDC);
	system("/bin/rm -f ".$destFilePathHostGroupHost);
	system("/bin/rm -f ".$destFilePathHostGroupIDC);
	$hostGroupContent="";	
	if ( count( $ipApiList ) === 0 )
		exit;
	$ipDict=array();
	$IDCDict=array();
	for ( $i = 0; $i < count( $ipApiList ); $i++ )
	{
		$tmpVal = explode(".total.", $ipApiList[ $i ] );
		$ip = $tmpVal[0];
		$idc = substr( $ip, 0, strrpos( $ip, "." ) );
		$tmpVal2 = explode(".",$tmpVal[1]);
		$api = $tmpVal2[0];
		array_push( $IDCDict, $idc );
		$tmpFileBody = str_replace( '_IP_', $ip, $cmdFileTmplBody );
		$tmpFileBody = str_replace( '_API_', $api, $tmpFileBody );
		
		if (  !array_key_exists( $ip, $ipDict ) )
		{
			$ipDict[$ip] = array();
			array_push( $ipDict[$ip], $api );
		}
		else
			array_push( $ipDict[$ip], $api );
		file_put_contents( $destFilePathService, $tmpFileBody, FILE_APPEND );
	}
//	print_r( $ipDict );
	while ( current( $ipDict ) !== False )
	{
		$serviceGroupItem=str_replace('_HOSTNAME_', key( $ipDict ), $hostMonitorTmpl);
		//print_r( $serviceGroupItem );
		$membersStr="";
		for ( $j = 0; $j < count( $ipDict[key( $ipDict ) ] ); $j++ )
		{
			if ( $j == 0 )
				$membersStr = str_replace( '_API_', key($ipDict).".".$ipDict[key($ipDict)][$j], $membersTmpl );
			else
				$membersStr = $membersStr.",".str_replace( '_API_', key($ipDict).".".$ipDict[key($ipDict)][$j], $membersTmpl );
		}
		$serviceGroupItem = str_replace( '_MEMBERS_', $membersStr, $serviceGroupItem );
		file_put_contents( $destFilePathHostGroupHost, $serviceGroupItem, FILE_APPEND );
		$tmpIPStr = str_replace('_IP_', key( $ipDict ), $cmdIPFileTmplBody );
		file_put_contents( $destFilePathServiceIP, $tmpIPStr, FILE_APPEND );
		next( $ipDict );
	}
	reset( $ipDict );
	$IDCDict = array_unique( $IDCDict );
	while( current( $IDCDict ) !== False )
	{
		//生成idc的监控项
		$tmpStr = str_replace('_IDC_', current( $IDCDict ), $cmdIDCFileTmplBody );
		file_put_contents( $destFilePathServiceIDC, $tmpStr, FILE_APPEND);


		//使用idc进行分组
               	$serviceGroupItem=str_replace('_HOSTNAME_', current($IDCDict), $hostMonitorTmpl);
		reset( $ipDict );
                $membersStr="";
		$i=0;
        	while ( current( $ipDict ) !== False )
        	{
                	//print_r( $serviceGroupItem );
                	for ( $j = 0; $j < count( $ipDict[key( $ipDict ) ] ); $j++ )
                	{
				if ( strpos( key( $ipDict ), current( $IDCDict ) ) === 0 )
				{
					//echo key( $ipDict ).":".current( $IDCDict )."\n";
                        		if ( $j == 0 && $i == 0 )
                               			$membersStr = str_replace( '_API_', key($ipDict).".".$ipDict[key($ipDict)][$j], $membersTmpl );
                        		else
                               			$membersStr = $membersStr.",".str_replace( '_API_', key($ipDict).".".$ipDict[key($ipDict)][$j], $membersTmpl );
				}
				else
					;//echo key( $ipDict ).":".current( $IDCDict )."\n";
                	}
			$i++;
                	next( $ipDict );
        	}
                if ( !Empty( $membersStr ) )
                {
		//	echo $serviceGroupItem."\n";
                	$serviceGroupItem = str_replace( '_MEMBERS_', $membersStr, $serviceGroupItem );
                        //echo $serviceGroupItem."\n";
                        file_put_contents( $destFilePathHostGroupIDC, $serviceGroupItem, FILE_APPEND );
                }
		next( $IDCDict );
	}
?>
