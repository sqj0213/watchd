<?php
	$keyList = "openapi.coreapi_yf.byhost.10_75_8_151*";
	$redisObj = new Redis('10.13.80.58', 6379 );
	print_r( $redisObj->keys( $keyList ) );

?>
