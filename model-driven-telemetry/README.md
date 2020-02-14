## Model Driven Telemetry
### Technology notes
I tested only on IOS-XE 17.1 and the notes below are written based on my experience with IOS-XE telemetry.  
[IOS-XE Programmability configuration guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/171/b_171_programmability_cg/model_driven_telemetry.html) is quite detailed document and has enough information to get started.  
With model-driven telemetry you can extract data in structured form (according to YANG models) from the device either periodically or on-change (if the model supports that). The list of IOS-XE YANG models which support on-change notification, can be found in YANG models github repo, e.g. [here](https://github.com/YangModels/yang/blob/master/vendor/cisco/xe/1711/ON_CHANGE_MODELS/ON_CHANGE_MODELS.MD) for 17.1. You can stream periodically any YANG data, not only operational, but also configuration data (e.g. stream the full config every hour).  
There are several main transport protocols which can be used for telemetry:
* NETCONF, which uses XML encoding, uses SSH
* gRPC, which uses google protocol buffer (protobuf) encoding. uses TCP or UDP (UDP is not supported by IOS-XE 17.1)
* gNMI (uses gRPC), which uses gRPC with HTTP/2, but encoding is JSON_IETF, has defined RPC operations (GetRequest/GetResponse/etc.), uses certificates for authentication

Streaming telemetry data encoding formats:
* XML
* JSON_IETF
* Google protobuf: not very human-readable but efficient, refer to [this article](https://blogs.cisco.com/sp/streaming-telemetry-with-google-protocol-buffers):
  * compact: keys are sent as integers according to ".proto" decoder file which should be present on both network device and the receiver. You need one ".proto" file for every path. The encoding is *very* efficient, but the need of the ".proto" files on the receiver makes it harder to use. As of 17.1, not supported by IOS-XE
  * key-value format: keys are sent as strings, requires a single general ".proto" file.

* TDL (I couldn't find a solid reference but it seems to be "Task description language") - format used by C9800 wireless controller to stream data to Cisco DNA Center.

There are two ways telemetry can be established:
* Dial-in: receiver establishes a session towards to the network device and asks devices to stream specific YANG data tree. If the session goes down (e.g. device reboots), it needs to be established again by the client. Used transport protocols: NETCONF and gNMI
* Dial-out: on the network device you configure what to stream and where and it will initiate a session to the receiver. It's usually in the running config, so it persists across reboots. This can usually be configured in CLI or using NETCONF/RESTCONF. The idea is similar to logging / netflow collector config. Used transport protocols: gRPC.

The most problematic part about telemetry is the amount of extra services you need to run to explore it. Here is a brief overview of existing tools (this is not my strong area so don't rely on the explanation below):
* Kafka - stream-processing tool, serves 3 purposes: message queue (read/write data stream), message broker (processes message with custom logic in realtime), data store (can temporarily store in-flight messages). Kafka can often be viewed as an intermediary in pub/sub model, where publisher(-s) pushes data and a subscriber(-s) can get this data. It can be deployed in a distributed fashion
* Apache Zookeeper - a service for maintaining configuration and synchronization for distributed systems. Kafka requires Zookeeper.
* Telegraf - is an agent for collecting, processing and aggregating metrics. It uses plugin system - you select input plugin which specifies the way data goes in (e.g. gRPC telemetry) and output plugin will write data to a data storage (usually, a time-series database). My understanding is that it is "kafka lite". It seems it was specifically designed for metrics.
* Time-series databases: databases designed to store and efficiently query data using timestamps. Perfect for metrics / events. Examples: OpenTSDB (seems to be not maintained anymore), InfluxDB, Prometheus.
* Grafana - analytics and monitoring tool, aka a dashboard with configurable alerts. Usually you feed data from a time-series database there. Supports multiple data storage options.
* Chronograf - dashboard + influxDB administration. Supports only InfluxDB storage.
* Kapacitor - data analytics + alerting tool. Has built-in alerting for Slack/Telegram and other tools.
* Elasticsearch - data storage designed mostly for data search and analytics. Stores data in JSON. Can be used to store and work with time-series data but technically is not a time-series database.
* Logstash - data processing (e.g. parsing) before sending data to elasticsearch
* Kibana - visualization + dashboard

You could have heard some combinations of these tools referred as "stack":
* TIG = Telegraf + InfluxDB + Grafana
* TICK = Telegraf + InfluxDB + Chronograf + Kapacitor
* Another popular choice is to replace influxDB with Prometheus in TIG stack (I don't think it is called TPG stack)
* ELK = Elasticsearch + Logstash + Kibana - as of February, 2020 I don't really see it being widely used for model driven telemetry, but I see it quite often used for software applications.

I don't have enough experience with these systems to evaluate which stack is better, so try multiple and see for yourself. Among all I like TICK stack the most - it's so easy to use. Telegram integration is slick too.

### Repository
#### grpc folder
Related to gRPC dial out telemetry.
Content:
* docker-compose.yml - describes services required to gather telemetry. It has both TIG and TICK stacks together. If you prefer only one, feel free to comment/delete services you don't need.
* telegraf/telegraf.conf - config file which is used by telegraf docker container. You may need to adjust ports if you make change to docker-compose file
* router.cfg - example of gRPC dial out config on the router

Instructions:
1) Start services to collect telemetry: `docker-compose up -d` (need docker/docker-compose installed)
2) Configure gRPC dial out on the router using CLI (refer to router.cfg)/NETCONF/RESTCONF. You can use `netconf/test_xpath.py` python script to test different xpath filters.
3) Check that the data if flowing into influxdb:
```
docker-compose exec influxdb influx
> use cisco_mdt
> show measurements  # you should see different tables
# you can use influx sql-like language it uses to query data, e.g.:
# select * from "Cisco-IOS-XE-memory-oper:memory-statistics/memory-statistic"
```
4) Log into chronograf (http://localhost:8888), or grafana (http://localhost:3000) (add influxdb (http://influxdb:8086) to grafana) and start building dashboards

#### netconf folder
For my stream I heavily used this: https://github.com/cisco-ie/telemetry_stacks  
Code examples are based on [`ncc-establish-subscription`](https://github.com/CiscoDevNet/ncc/blob/master/ncc-establish-subscription.py) by [Einar Nilsen-Nygaard](https://github.com/einarnn). Uses Python 3.7 and [fork (!)](https://github.com/CiscoDevNet/ncc) of `ncclient` maintained by Einar too. Currently original `ncclient` does not implement `establish_subscription` RPC call, so if you want to use the original `ncclient`, you will need to construct RPC manually. This fork dependency is reflected in `pyproject.toml`/`requirements.txt`.
* code/constants.py - contains connection details to your IOS-XE device. Adjust to your lab.
* code/utils.py - contains some helper functions
* code/test_xpath.py - script you can run, it can help you with exploring if your xpath is valid. Useful for both NETCONF dial-in and gRPC dial out telemetry
* code/nc_dial_in_subscribe.py - script which will subscribe to provided xpath via NETCONF and send data to kafka (if `telemetry.kafka_callback` is used) or will just print on the stdout (if `telemetry.print_callback` is used)
* rpc-examples directory - contains NETCONF RPC examples to establish subscription (useful for raw interaction with NETCONF server in the terminal)

Instructions:
1) configure NETCONF on the network device with: `netconf-yang`
2) Verify that NETCONF is working and you can establish subscription manually:
```
ssh cisco@192.168.153.101 -p 830 -s netconf
# send hello rpc (copy rpc-examples/hello.xml to the terminal)
# send on-change or periodic subscription rpc and see data flowing back
```
3) Start services to collect telemetry: `docker-compose up -d` (need docker/docker-compose installed)
4) Create Python virtual environment/install dependencies from `pyproject.toml`/`requirements.txt`
5) Run script: `python nc_dial_in_subscribe.py`, you will see output on the stdout.
6) You can change `print_callback` to `kafka_callback` and re-run it. You will not see output on the screen, the data is now seen in kafka docker container logs. However, the data will not get into OpenTSDB because you need a kafka sink connector to do that. On the stream I was using jupyter spark notebook (taken from https://github.com/cisco-ie/telemetry_stacks) for that, but I think it is quite clunky. So there is some gap here. You can probably write your own connector (or find an existing implementation).

#### Streams
So far I had two streams about telemetry:
* Streaming Telemetry NETCONF dial-in: https://youtu.be/E_em9yiIUeU
* Streaming Telemetry gRPC dial-out: https://youtu.be/SxUzY_hD0iM


#### Resources
* Model-Driven Telemetry Configuration Guide IOS-XE 17.1: https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/171/b_171_programmability_cg/model_driven_telemetry.html
* YANG models: https://github.com/YangModels
* DevNet Telemetry Sandbox: https://devnetsandbox.cisco.com/RM/Diagram/Index/0e053963-b039-4a15-94f6-54db2f5ad61c?diagramType=Topology
* DevNet Model-Driven Telemetry learning lab: https://developer.cisco.com/learning/modules/iosxe_telemetry
* Streaming Telemetry with Google protocol buffers (blog): https://blogs.cisco.com/sp/streaming-telemetry-with-google-protocol-buffers