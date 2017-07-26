/*jshint node:true, laxcomma:true */

/*
 * Flush stats to graphite (http://graphite.wikidot.com/).
 *
 * To enable this backend, include 'graphite' in the backends
 * configuration array:
 *
 *   backends: ['graphite']
 *
 * This backend supports the following config options:
 *
 *   graphiteHost: Hostname of graphite server.
 *   graphitePort: Port to contact graphite server at.
 */

var net = require('net');

// this will be instantiated to the logger
var l;

var debug;
var flushInterval;
var graphiteHost;
var graphitePort;
var flush_counts;

// prefix configuration
var globalPrefix;
var prefixCounter;
var prefixTimer;
var prefixGauge;
var prefixSet;
var globalSuffix;
var prefixStats;
var globalKeySanitize = true;

// set up namespaces
var legacyNamespace  = true;
var globalNamespace  = [];
var counterNamespace = [];
var timerNamespace   = [];
var gaugesNamespace  = [];
var setsNamespace    = [];

var graphiteStats = {};

var post_stats = function graphite_post_stats(statString) {
  var last_flush = graphiteStats.last_flush || 0;
  var last_exception = graphiteStats.last_exception || 0;
  var flush_time = graphiteStats.flush_time || 0;
  var flush_length = graphiteStats.flush_length || 0;
  if (graphiteHost) {
    try {
      var graphite = net.createConnection(graphitePort, graphiteHost);
      graphite.addListener('error', function(connectionException){
        if (debug) {
          l.log(connectionException);
        }
      });
      graphite.on('connect', function() {
        var ts = Math.round(new Date().getTime() / 1000);
        var ts_suffix = ' ' + ts + "\n";
        var namespace = globalNamespace.concat(prefixStats).join(".");
        statString += namespace + '.graphiteStats.last_exception' + globalSuffix + last_exception + ts_suffix;
        statString += namespace + '.graphiteStats.last_flush'     + globalSuffix + last_flush     + ts_suffix;
        statString += namespace + '.graphiteStats.flush_time'     + globalSuffix + flush_time     + ts_suffix;
        statString += namespace + '.graphiteStats.flush_length'   + globalSuffix + flush_length   + ts_suffix;

        var starttime = Date.now();
        this.write(statString);
        this.end();
        graphiteStats.flush_time = (Date.now() - starttime);
        graphiteStats.flush_length = statString.length;
        graphiteStats.last_flush = Math.round(new Date().getTime() / 1000);
      });
    } catch(e){
      if (debug) {
        l.log(e);
      }
      graphiteStats.last_exception = Math.round(new Date().getTime() / 1000);
    }
  }
};

var flush_stats = function graphite_flush(ts, metrics) {
  var ts_suffix = ' ' + ts + "\n";
  var starttime = Date.now();
  var statString = '';
  var numStats = 0;
  var key;
  var timer_data_key;
  var counters = metrics.counters;
  var gauges = metrics.gauges;
  var timers = metrics.timers;
  var sets = metrics.sets;
  var counter_rates = metrics.counter_rates;
  var timer_data = metrics.timer_data;
  var statsd_metrics = metrics.statsd_metrics;

  var t1 = (new Date).getTime();
  // Sanitize key for graphite if not done globally
  function sk(key) {
    if (globalKeySanitize) {
      return key;
    } else {
      return key.replace(/\s+/g, '_')
                .replace(/\//g, '-')
                .replace(/[^a-zA-Z_\-0-9\.]/g, '');
    }
  };

  for (key in counters) {
    var value = counters[key];
    var valuePerSecond = counter_rates[key]; // pre-calculated "per second" rate
    var keyName = sk(key);
    var namespace = counterNamespace.concat(keyName);
    var hitsNamespace = globalNamespace.concat(keyName);

    if (legacyNamespace === true) {
      statString += hitsNamespace.join(".")   + globalSuffix + valuePerSecond + ts_suffix;
      if (flush_counts) {
        statString +=  counterNamespace.join('.') +"."+ keyName + globalSuffix + value + ts_suffix;
      }
    } else {
      statString += namespace.concat('rate').join(".")  + globalSuffix + valuePerSecond + ts_suffix;
      if (flush_counts) {
        statString += namespace.concat('count').join(".") + globalSuffix + value + ts_suffix;
      }
    }

    numStats += 1;
  }

  var t2 = (new Date).getTime();
  var t3 = (new Date).getTime();
  for (key in timer_data) {
    var namespace = timerNamespace.concat(sk(key));
    var the_key = namespace.join(".");

    for (timer_data_key in timer_data[key]) {
      if (typeof(timer_data[key][timer_data_key]) === 'number') {
        statString += the_key + '.' + timer_data_key + globalSuffix + timer_data[key][timer_data_key] + ts_suffix;
      } else {
        for (var timer_data_sub_key in timer_data[key][timer_data_key]) {
          statString += the_key + '.' + timer_data_key + '.' + timer_data_sub_key + globalSuffix +
                        timer_data[key][timer_data_key][timer_data_sub_key] + ts_suffix;
        }
      }
    }
    numStats += 1;
  }

  for (key in gauges) {
    var namespace = gaugesNamespace.concat(sk(key));
    statString += namespace.join(".") + globalSuffix + gauges[key] + ts_suffix;
    numStats += 1;
  }

  for (key in sets) {
    var namespace = setsNamespace.concat(sk(key));
    statString += namespace.join(".") + '.count' + globalSuffix + sets[key].values().length + ts_suffix;
    numStats += 1;
  }

  var namespace = globalNamespace.concat(prefixStats);
  if (legacyNamespace === true) {
    statString += prefixStats + '.numStats' + globalSuffix + numStats + ts_suffix;
    statString += 'stats.' + prefixStats + '.graphiteStats.calculationtime' + globalSuffix + (Date.now() - starttime) + ts_suffix;
    for (key in statsd_metrics) {
      statString += 'stats.' + prefixStats + '.' + key + globalSuffix + statsd_metrics[key] + ts_suffix;
    }
  } else {
    statString += namespace.join(".") + '.numStats' + globalSuffix + numStats + ts_suffix;
    statString += namespace.join(".") + '.graphiteStats.calculationtime' + globalSuffix + (Date.now() - starttime) + ts_suffix;
    for (key in statsd_metrics) {
      var the_key = namespace.concat(key);
      statString += the_key.join(".") + globalSuffix + statsd_metrics[key] + ts_suffix;
    }
  }
  var t4 = (new Date).getTime();
  var t5 = (new Date).getTime();
  post_stats(statString);
  var t6 = (new Date).getTime();
  if (debug) {
   l.log("t6-t5="+(t6-t5)+",t4-t3="+(t4-t3)+",t2-t1="+(t2-t1)+",numStats: " + numStats);
  }
};

var backend_status = function graphite_status(writeCb) {
  for (var stat in graphiteStats) {
    writeCb(null, 'graphite', stat, graphiteStats[stat]);
  }
};

exports.init = function graphite_init(startup_time, config, events, logger) {
  debug = config.debug;
  l = logger;
  graphiteHost = config.graphiteHost;
  graphitePort = config.graphitePort;
  config.graphite = config.graphite || {};
  globalPrefix    = config.graphite.globalPrefix;
  prefixCounter   = config.graphite.prefixCounter;
  prefixTimer     = config.graphite.prefixTimer;
  prefixGauge     = config.graphite.prefixGauge;
  prefixSet       = config.graphite.prefixSet;
  globalSuffix    = config.graphite.globalSuffix;
  legacyNamespace = config.graphite.legacyNamespace;
  prefixStats     = config.prefixStats;

  // set defaults for prefixes & suffix
  globalPrefix  = globalPrefix !== undefined ? globalPrefix : "stats";
  prefixCounter = prefixCounter !== undefined ? prefixCounter : "counters";
  prefixTimer   = prefixTimer !== undefined ? prefixTimer : "timers";
  prefixGauge   = prefixGauge !== undefined ? prefixGauge : "gauges";
  prefixSet     = prefixSet !== undefined ? prefixSet : "sets";
  prefixStats   = prefixStats !== undefined ? prefixStats : "statsd";
  legacyNamespace = legacyNamespace !== undefined ? legacyNamespace : true;

  // In order to unconditionally add this string, it either needs to be
  // a single space if it was unset, OR surrounded by a . and a space if
  // it was set.
  globalSuffix  = globalSuffix !== undefined ? '.' + globalSuffix + ' ' : ' ';

  if (legacyNamespace === false) {
    if (globalPrefix !== "") {
      globalNamespace.push(globalPrefix);
      counterNamespace.push(globalPrefix);
      timerNamespace.push(globalPrefix);
      gaugesNamespace.push(globalPrefix);
      setsNamespace.push(globalPrefix);
    }

    if (prefixCounter !== "") {
      counterNamespace.push(prefixCounter);
    }
    if (prefixTimer !== "") {
      timerNamespace.push(prefixTimer);
    }
    if (prefixGauge !== "") {
      gaugesNamespace.push(prefixGauge);
    }
    if (prefixSet !== "") {
      setsNamespace.push(prefixSet);
    }
  } else {
      //globalNamespace = ['stats'];
      //counterNamespace = ['stats'];
      globalNamespace = ['stats_byhost'];
      counterNamespace = ['stats_byhost','counts'];
      timerNamespace = ['stats_byhost', 'timers'];
      gaugesNamespace = ['stats_byhost', 'gauges'];
      setsNamespace = ['stats_byhost', 'sets'];
  }

  graphiteStats.last_flush = startup_time;
  graphiteStats.last_exception = startup_time;
  graphiteStats.flush_time = 0;
  graphiteStats.flush_length = 0;

  if (config.keyNameSanitize !== undefined) {
    globalKeySanitize = config.keyNameSanitize;
  }

  flushInterval = config.flushInterval;

  flush_counts = typeof(config.flush_counts) === "undefined" ? true : config.flush_counts;

  events.on('flush', flush_stats);
  events.on('status', backend_status);

  return true;
};
