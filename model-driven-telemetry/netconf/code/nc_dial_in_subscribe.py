#!/usr/bin/env python
import sys
import signal
from ncclient import manager
from lxml import etree
from kafka import KafkaProducer
import jxmlease
import json
import logging
import time

import constants

KAFKA_URL = "localhost:9092"
HOST = "192.168.153.101"

class TelemetryIOSXE:
    def __init__(self, host, username, password,
                 verbose=False):
        self.host = host
        self.username = username
        self.password = password
        if verbose:
            self.logging()
        # self.connect()
        # self.kafka_connect()
        self.nc_conn = None
        self.producer = None
        self.sub = None


    def nc_connect(self):
        self.nc_conn = manager.connect(
            host=self.host,
            username=self.username,
            password=self.password,
            device_params={'name':'csr'},
            hostkey_verify=False,
            allow_agent=False,
            unknown_host_cb=self.unknown_host_cb
        )

    def close(self) -> None:
        if self.nc_conn:
            if self.sub:
                try:
                    nc_reply = self.nc_conn.delete_subscription(self.sub.subscription_id)
                    print(f"subscription successfully deleted: {nc_reply.subscription_result}")
                except:
                    pass
            self.nc_conn.close_session()
        self.nc_conn = None
        if self.producer:
            self.producer.close()
        self.producer = None

    def __enter__(self):
        self.nc_connect()
        self.kafka_connect()
        return self

    def __exit__(self, *args):
        self.close()

    def sigint_handler(self, signal, frame):
        self.close()
        sys.exit(0)

    def print_callback(self, notif):
        data = etree.tostring(notif.datastore_ele, pretty_print=True).decode("utf-8")
        result = (
            f"-->>\n"
            f"Event time      : {notif.event_time}\n"
            f"Subscription Id : {notif.subscription_id}\n"
            f"Type            : {notif.type}\n"
            f"Data            :\n{data}\n"
            f"<<--"
        )
        print(result)

    def kafka_connect(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    def kafka_callback(self, notif):
        data = json.loads(json.dumps(jxmlease.parse(notif.xml)))
        self.producer.send('telemetryxe', data['notification'])

    def errback(self, notif):
        pass

    def unknown_host_cb(self, host, fingerprint):
        return True

    def establish_sub(self, xpath, callback, period=None, dampening_period=None):
        sub = self.nc_conn.establish_subscription(
            callback,
            self.errback,
            xpath=xpath,
            period=period,
            dampening_period=dampening_period
        )
        s = (
            f"Subscription Result : {sub.subscription_result}\n"
            f"Subscription Id     : {sub.subscription_id}"
        )
        print(s)
        self.sub = sub

    def single_sub(self, xpath, callback, period):
        self.establish_sub(xpath, callback=callback, period=period)
        while True:
            time.sleep(0.5)

    def multi_sub(self, xpath_list, callback):
        for item in xpath_list:
            self.establish_sub(callback=callback, **item)
        while True:
            time.sleep(0.5)

    def logging(self):
        handler = logging.StreamHandler()
        for l in ['ncclient.transport.session', 'ncclient.operations.rpc']:
            logger = logging.getLogger(l)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    with TelemetryIOSXE(**constants.NC_CONN_PARAMS) as telemetry:
        # xpath = '/process-cpu-ios-xe-oper:cpu-usage/process-cpu-ios-xe-oper:cpu-utilization/process-cpu-ios-xe-oper:five-seconds'
        xpath = "/platform-sw-ios-xe-oper:cisco-platform-software/control-processes/control-process/per-core-stats/per-core-stat"
        # xpath = '/process-memory-ios-xe-oper:memory-statistics'
        # xpath = '/if:interfaces-state/if:interface/if:statistics'
        # xpath = '/bgp-ios-xe-oper:bgp-state-data/bgp-ios-xe-oper:neighbors'
        # xpath = '/if:interfaces-state/if:interface[name="GigabitEthernet1"]/if:statistics'
        # xpath = '/oc-acl:acl/acl-sets'
        # xpath = '/oc-acl:acl/acl-sets/acl-set[name="PERMIT-EVERYTHING" and type="ACL_IPV4"]/acl-entries'
        # xpath = '/ios:native/vrf'
        telemetry.single_sub(
            xpath,
            # callback=telemetry.kafka_callback,
            callback=telemetry.print_callback,
            period=3000
        )

        # xpaths_list = [
        #     {"xpath": '/process-cpu-ios-xe-oper:cpu-usage/process-cpu-ios-xe-oper:cpu-utilization/process-cpu-ios-xe-oper:five-seconds', "period": 1000},
        #     {"xpath": '/if:interfaces-state/if:interface/if:statistics', "period": 1000},
        #     {"xpath": '/bgp-state-data', "period": 1000}
        # ]
        # telemetry.multi_sub(
        #     xpaths_list,
        #     # callback=telemetry.kafka_callback,
        #     callback=telemetry.print_callback,
        # )
