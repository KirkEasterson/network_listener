import os


class ptfGenerator:

    className = ""

    commands = ()
    hosts = set()
    switches = set()
    controllers = set()
    links = set()

    macs = {}
    pings = {}

    def __init__(self, className, commands, hosts, switches, controllers, links, macs, ips, pings):
        self.className = className
        self.commands = commands
        self.hosts = hosts
        self.switches = switches
        self.controllers = controllers
        self.links = links
        self.macs = macs
        self.ips = ips
        self.pings = pings

    def generatePreamble(self):
        return """import time
import logging
import ptf.dataplane as dataplane
import sai_base_test
from ptf.testutils import *
from switch_sai_thrift.ttypes import  *
from ptf.mask import Mask
"""

    def initializeVariables(self):
        return """
switch_inited=0
port_list = []
table_attr_list = []
"""

    def generateClassDefinition(self):
        return """
class {className}(sai_base_test.SAIThriftDataplaneTest):
""".format(className=self.className)

    def createPing(self, src, dst):
        mac1=self.macs[src]
        mac2=self.macs[dst]
        ip_dst = self.ips[dst].split("/")[0]
        return """
        print(\"Sending packet from {src} to {dst}\")
        switch_init(self.client) # Need help with this
        #port1 = \"port1\"
        #port2 = \"port2\"
        mac1 = \"{mac1}\"
        mac2 = \"{mac2}\"
        mac_action = 1

        self.client.sai_thrift_create_vlan(vlan_id)
        vlan_port1 = sai_thrift_vlan_port_t(port_id=port1, tagging_mode=0)
        vlan_port2 = sai_thrift_vlan_port_t(port_id=port2, tagging_mode=0)
        self.client.sai_thrift_add_ports_to_vlan(vlan_id, [vlan_port1, vlan_port2])

        sai_thrift_create_fdb(self.client, vlan_id, mac1, port1, mac_action)
        sai_thrift_create_fdb(self.client, vlan_id, mac2, port2, mac_action)

        pkt = simple_tcp_packet(eth_dst=\"{mac1}\",
                                eth_src=\"{mac2}\",
                                ip_dst=\"{ip_dst}\",
                                ip_id=101,
                                ip_ttl=64)

        try:
            # in tuple: 0 is device number, 2 is port number
            # this tuple uniquely identifies a port
            send_packet(self, (0, 2), pkt)
            verify_packets(self, pkt, device_number=0, ports=[1])
            # or simply
            # send_packet(self, 2, pkt)
            # verify_packets(self, pkt, ports=[1])
        finally:
            sai_thrift_delete_fdb(self.client, vlan_id, mac1, port1)
            sai_thrift_delete_fdb(self.client, vlan_id, mac2, port2)

            self.client.sai_thrift_remove_ports_from_vlan(vlan_id, [vlan_port1, vlan_port2])
            self.client.sai_thrift_delete_vlan(vlan_id)
""".format(src=src, dst=dst, mac1=mac1, mac2=mac2, ip_dst=ip_dst)

    def generateRunTestMethod(self):
        result = """
    def runTest(self):
"""
        for ping in self.pings:
            (src, dst) = ping
            result += self.createPing(src, dst)
        return result


    def generate(self):
        file = open(self.className+".py", "w")
        file.write(self.generatePreamble())
        file.write(self.initializeVariables())
        file.write(self.generateClassDefinition())
        file.write(self.generateRunTestMethod())
        file.close()
