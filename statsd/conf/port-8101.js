{
  graphitePort: 2003
, graphiteHost: "10.13.81.28"
, port: 8101
, mgmt_port: 8101
, title: "statsd"
, deleteIdleStats: true
, flush_counts: false
, deleteGauges: true
, deleteTimers: true
, deleteCounters: true
, deleteSets: true
, prefixStats: "statsd.10_13_81_22.8101"
, backends: [ "./backends/graphite" ]
}
