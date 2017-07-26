
#num=0
for((ii=1;ii<=1;ii++));do
    echo "start"
    #$num=$num + 1*10
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.total._1_test_remind_set_count_json.hits --host 10.13.80.58 --port 8125
    done;
    #5xx
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_5xx._1_test_remind_set_count_json.hits --host 10.13.80.58 --port 8125
    done;
    #4xx
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_4xx._1_test_remind_set_count_json.hits --host 10.13.80.58 --port 8125
    done;
    #2xx
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_2xx._1_test_remind_set_count_json.hits --host 10.13.80.58 --port 8125
    done;
    #less_500
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_2xx._1_test_remind_set_count_json.less_500ms --host 10.13.80.58 --port 8125
    done;
    #less 1s
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_2xx._1_test_remind_set_count_json.less_1s --host 10.13.80.58 --port 8125
    done;
    #less 2s
    for((i=1;i<=10;i++));do
    python statsd-client.py --key test.test_yf.byhost.1_1_1_1.http_2xx._1_test_remind_set_count_json.less_2s --host 10.13.80.58 --port 8125
    done;
    #less 4s
    for((i=1;i<=10;i++));do
    python statsd-client.py --key openapi.blossomin_yf.byhost.1_1_1_1.http_2xx._1_test_remind_set_count_json.less_4s --host 10.13.80.58 --port 8125
    done;
    #echo $num
done;