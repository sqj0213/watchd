from pystatsd import Client;
import argparse;
parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", help="please input statsd server ip or domain name default localhost" )
parser.add_argument("--port", type=int, default=8125, help="please input statsd server port default 8125" )
parser.add_argument("--value", type=int, default=1, help="please input statsd server option keyvalue default 1" )
parser.add_argument("--option", type=str, default="count", help="please input statsd server option key type default count(count/timer)" )
parser.add_argument("--key", type=str, default="key", help="please input statsd server option key " )
args = parser.parse_args()
clientObj = Client(args.host, args.port);
if ( args.option == "count" ):
	clientObj.increment( args.key )
elif ( args.option == "timer" ):
	clientObj.timing( args.key, args.value )
else:
	print "parameter failed!";

