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
        return """
import time
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
        return """
        print(\"Sending packet from {src} to {dst}\")
        switch_init(self.client) # Need help with this
        #port1 = \"port1\"
        #port2 = \"port2\"
        mac1 = \"{mac1}\"
        mac2 = \"{mac2}\"

        pkt = simple_tcp_packet(eth_dst=\"{mac1}\",
                                eth_src=\"{mac2}\",
                                ip_dst=\"{ip_dst}\",
                                ip_id=101,
                                ip_ttl=64)

        try:
            send_packet(self, (0, 2), pkt)
            verify_packets(self, pkt, device_number=0, ports=[1])
        finally:
            # Some sort of cleanup

""".format(src=src, dst=dst, mac1=self.macs[src], mac2=self.macs[dst], ip_dst=self.ips[dst])

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
