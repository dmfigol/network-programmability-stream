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


class TelemetryIOSXE:
    def __init__(self, host, username='admin', password='Cisco1234!', port=830,
                 verbose=False, delete_after=None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        if verbose:
            self.logging()
        self.delete_after = delete_after
        self.connect()
        self.kafka_connect()

    def sigint_handler(self, signal, frame):
        self.man.close_session()
        sys.exit(0)

    def callback(self, notif):
        print('-->>')
        print('Event time      : %s' % notif.event_time)
        print('Subscription Id : %d' % notif.subscription_id)
        print('Type            : %d' % notif.type)
        print('Data            :')
        print(etree.tostring(notif.datastore_ele, pretty_print=True))
        print('<<--')

    def kafka_connect(self):
        self.producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    def kafka_callback(self, notif):
        data = json.loads(json.dumps(jxmlease.parse(notif.xml)))
        print(data)
        #self.producer.send('telemetryxe', data['notification'])

    def errback(self, notif):
        pass

    def unknown_host_cb(self, host, fingerprint):
            return True

    def connect(self):
        self.man = manager.connect(host=self.host,
                                   port=self.port,
                                   username=self.username,
                                   password=self.password,
                                   allow_agent=False,
                                   look_for_keys=False,
                                   hostkey_verify=False,
                                   unknown_host_cb=self.unknown_host_cb)

    def establish_sub(self, xpath, period=None, dampening_period=None):
        self.sub = self.man.establish_subscription(
            self.callback,
            self.errback,
            xpath=xpath,
            period=period,
            dampening_period=dampening_period)
        print('Subscription Result : %s' % self.sub.subscription_result)
        print('Subscription Id     : %d' % self.sub.subscription_id)

    def wait_for(self):
        if self.delete_after:
            time.sleep(self.delete_after)
            r = self.man.delete_subscription(self.sub.subscription_id)
            print('delete subscription result = %s' % r.subscription_result)
        else:
            while True:
                time.sleep(5)

    def single_sub(self, xpath, **args):
        signal.signal(signal.SIGINT, self.sigint_handler)
        self.establish_sub(xpath, **args)
        self.wait_for()

    def multi_sub(self, xpath_list):
        signal.signal(signal.SIGINT, self.sigint_handler)
        for item in xpath_list:
            self.establish_sub(**item)
        self.wait_for()

    def logging(self):
        handler = logging.StreamHandler()
        for l in ['ncclient.transport.session', 'ncclient.operations.rpc']:
            logger = logging.getLogger(l)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    telem = TelemetryIOSXE(host='10.10.20.30')
    # xpath = '/if:interfaces-state/if:interface[name="GigabitEthernet1"]/if:statistics'
    # xpath = '/oc-acl:acl/acl-sets'
    # xpath = '/oc-acl:acl/acl-sets/acl-set[name="PERMIT-EVERYTHING" and type="ACL_IPV4"]/acl-entries'
    xpath = '/ios:native/vrf'
    telem.single_sub(xpath, period=3000)
