import os

class ptfGenerator:

    filename = ""
    className = ""

    comman1ds = ()
    hosts = set()
    switches = set()
    controllers = set()
    links = set()

    def __init__(self, filename, commands, hosts, switches, controllers, links):
        self.filename = filename

    def setData(self, commands, hosts, switches, controllers, links):
        self.commands = commands
        self.hosts = hosts
        self.switches = switches
        self.controllers = controllers
        self.links = links

    def generatePremble(self):
        return """
import ptf
from ptf.base_tests import BaseTest
from ptf import config
import ptf.testutils as testutils

import switch_sai_thrift
import switch_sai_thrift.switch_sai_rpc as switch_sai_rpc

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class {className}(BaseTest):
""".format(className=self.className)

    def generateTestMethod(self):
        return ""

    def runTest(self, testDir, interfaces):

        # Create the required veths
        os.system("""cd $P4FACTORY/tools/
            sudo ./veth_setup.sh""")

        # Compile the target switch and run it
        os.system("""cd $P4FACTORY/targets/switch/
            make bm-switchsai
            sudo ./behavioral-model""")

        # Run the test
        command = """cd $PTF/
            sudo ./ptf --test-dir {testDir} --pypath $PWD"""
        for interface in interfaces:
            command += " --interface "+interface
        os.system(command)
