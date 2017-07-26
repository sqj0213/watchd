<?php
/* 
 * 从nagios获取报警数据脚本
 * 调用 nagios的./includes/utils.inc.php   
 * read_status_file_to_monitor()函数读取/data0/nagios/status.dat 数据文件
 */
require_once('./includes/utils.inc.php');
$key = $_GET["key"];
$value =  $_GET["value"];

if(empty($key)||empty($value)){
	echo "Example: php reqNagiosStatus.php -k idc -v openapi.coreapi_yf";
	return 0;
}


$dataList = read_status_file_to_monitor('/data0/nagios/status.dat' );
$contents=array(
    "key" =>$key,
    "value" =>$value,
    "idc" => array(),
    "ip" => array(),
    "ipapi" => array()
);
$statustype="unknown";
$current_idc=0;
$current_ip=0;
$current_ipapi=0;
foreach( $dataList["servicestatus"] as $data){
    if( $key == "idc" ){
	    if( strpos( $data["service_description"], $value) !==  False && strpos( $data["service_description"], "byhost")==  False){
	        $contents[$key][$current_idc]=$data;
	        $current_idc++;
	        continue;
	    }
	    if( strpos( $data["service_description"], $value.".byhost.") !==  False ){
	    	$item=explode(".byhost.",$data["service_description"]);
	    	if( strpos( $item[1],".") ==  False  ){
		        $contents["ip"][$current_ip]=$data;
		        $current_ip++;
		        continue;
		    }else{
		    	$contents["ipapi"][$current_ipapi]=$data;
		        $current_ipapi++;
		        continue;
		    }
	    }
	}
	if( $key == "ip" ){
        if( strpos( $data["service_description"], $value) !==  False &&  strpos( $data["service_description"], $value.".") ===  False){
	        $contents["ip"][$current_ip]=$data;
	        $current_ip++;
	        continue;
	    }
	    if( strpos( $data["service_description"], $value) !==  False &&  strpos( $data["service_description"], $value.".") !==  False){
	        $contents["ipapi"][$current_ipapi]=$data;
	        $current_ipapi++;
	        continue;
	    }
	}
	if( $key == "api" ){
        if( strpos( $data["service_description"], $value) !==  False){
	        $contents["ipapi"][$current_ipapi]=$data;
	        $current_ipapi++;
	        continue;
	    }
	}

}
header('Access-Control-Allow-Origin: *');
header('Content-Type:application/json; charset=UTF-8');
echo json_encode($contents);
