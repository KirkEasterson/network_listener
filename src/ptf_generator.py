import os
import math
import ipaddress
import random


class PythonGenerator:

    fileName = ""

    def __init__(self, fileName):
        self.fileName = fileName

    def writeToFile(self, code):
        file = open(self.fileName, "w")
        file.write(code)
        file.close()
    

    def generateBlankLine(self, n=1):
        return "\n"*n

    def indentCode(self, code, level=0):
        result = ""
        indentation = "\t"*level
        for line in code.split("\n"):
            result += "{}{}\n".format(indentation, line)
        return result

    def addComment(self, comment, level=0):
        commented = ""
        for line in comment.split("\n"):
            commented += "# {}".format(line)
        return self.indentCode(commented, level)

    def generateImport(self, importValue, fromValue="", asValue="", level=0):
        fromPortion = "from {} ".format(fromValue) if (fromValue) else ""
        asPortion = " as {}".format(asValue) if (asValue) else ""
        importLine = "{}import {}{}".format(
            fromPortion, importValue, asPortion)
        return self.indentCode(importLine, level)

    # imports is an array of tuples containing (importValue, fromvalue, asValue)
    # this doesn't read like a usual python import, but makes it easy to allow for
    #   optional "from ..." and "... as ..." values

    def generatePreamble(self, imports, level=0, mode=None):
        preamble = ""
        for (importValue, fromValue, asValue) in imports:
            preamble += self.generateImport(importValue, fromValue, asValue)
        
        if (mode == "test"):
            preamble += self.generateBlankLine()
            preamble += "sys.stdout = open('ptf_generator_stdout.txt', 'w')\n"
            preamble += "sys.stderr = open('ptf_generator_stdout.txt', 'w')"
        return self.indentCode(preamble, level)

    def assignVariable(self, varName, value, level=0):
        variable = """{} = {}""".format(varName, value)
        return self.indentCode(variable, level)

    # vars is an array of tuples containing (name, value)
    # this makes it easy to declare many variables at once, but also allowing the flexibility of only declaring one variable

    def assignVariables(self, vars, level=0):
        variableLine = ""
        for (varName, varValue) in vars:
            variableLine += self.assignVariable(varName, varValue)
        return self.indentCode(variableLine, level)

    def generateClassDefinition(self, className, superClass="", level=0):
        superClassPortion = "({})".format(superClass) if superClass else ""
        classDef = "class {}{}:\n".format(className, superClassPortion)
        return self.indentCode(classDef, level)

    # args is an array of tuples containing (argName, defaultValue)

    def generateMethodDefinition(self, methodName, args=[], level=0):
        methodArgs = "self"
        for (argName, defaultValue) in args:
            methodArgs += ", {argName}".format(argName)
            if (defaultValue):
                methodArgs += "={}".format(defaultValue)
        methodDef = """def {}({}):""".format(methodName, methodArgs)
        return self.indentCode(methodDef, level)

    def generateCodeBlock(self, block, level=0):
        return self.indentCode(block, level)


class PtfGenerator(PythonGenerator):

    NETWORK_SIZE = 256 # number of addresses on each network
    SUBNET_MASK = 32 - int(math.floor(math.log(NETWORK_SIZE, 2)))
    NETWORK_SEED = 167772160 # 10.0.0.0 in binary in decimal

    networks = {}

    mode = None

    commands = ()
    hosts = set()
    switches = set()
    controllers = set()
    links = set()

    macs = {}
    ips = {}
    pings = {}

    socketStates = None

    addrs = set()

    pubs = {}
    subs = {}
    broadcasts = {}

    dataSends = []
    dataRecvs = []

    def random_bytes(self, num=6):
        return [random.randrange(256) for _ in range(num)]

    # def generate_mac(self, uaa=False, multicast=False, oui=None, separator=':', byte_fmt='%02x'):
    def generate_mac(self):
        mac = self.random_bytes()
        # if oui:
        #     if type(oui) == str:
        #         oui = [int(chunk) for chunk in oui.split(separator)]
        #     mac = oui + random_bytes(num=6-len(oui))
        # else:
        #     if multicast:
        #         mac[0] |= 1 # set bit 0
        #     else:
        #         mac[0] &= ~1 # clear bit 0
        #     if uaa:
        #         mac[0] &= ~(1 << 1) # clear bit 1
        #     else:
        #         mac[0] |= 1 << 1 # set bit 1
        return ':'.join('%02x' % b for b in mac)

    def create_networks(self, addrs):
        curr_network = self.NETWORK_SEED
        for addr in addrs:
            self.networks[addr] = (ipaddress.ip_network((curr_network, self.SUBNET_MASK)), 0)
            curr_network += self.NETWORK_SIZE

    def add_pubs(self, pubs):
        for pub in pubs:
            socketState = self.socketStates[pub]
            addr = socketState.addr
            (ip_network_addr, num_hosts) = self.networks[addr]
            ip_host_addr = ip_network_addr + num_hosts + 1
            self.pubs[socketState.id] = ipaddress.ip_address(ip_host_addr)
            
            ip_broadcast_addr = ip_network_addr + self.NETWORK_SIZE - 1 # broadcast address for the network
            self.broadcasts[ip_network_addr] = ip_broadcast_addr
            # self.macs[socketState.socketId] = self.generate_mac()
    
    def add_subs(self, subs):
        for sub in subs:
            socketState = self.socketStates[sub]
            addr = socketState.addr
            (ip_network_addr, _) = self.networks[addr]
            ip_host_addr = int(ip_network_addr) + self.NETWORK_SIZE - 1 # broadcast address for the network
            self.subs[socketState.id] = ipaddress.ip_address(ip_host_addr)
            # self.macs[socketState.socketId] = self.generate_mac()
    
    def __init__(self, fileName, mode, socketStates, addrs, pubs, subs, dataSends, dataRecvs):
        PythonGenerator.__init__(self, fileName)
        self.mode = mode
        self.socketStates = socketStates
        self.dataSends = dataSends
        self.dataRecvs = dataRecvs
        self.create_networks(addrs)
        self.add_pubs(pubs)
        # self.add_subs(subs)
        self.subs = subs

    def createPacket(self, pktName, src, dst, level=0):
        pkt = """
print(\"Sending packet - {src} -> {dst}\")
{pktName} = testutils.simple_tcp_packet(
                        eth_src=macs[\"{src}\"],
                        eth_dst=macs[\"{dst}\"],
                        ip_src=ips[\"{src}\"],
                        ip_dst=ips[\"{dst}\"])
pkts.append({pktName})
""".format(pktName=pktName, src=src, dst=dst)
        return self.indentCode(pkt, level)

    # packets is a list containing the variable names of all the packets

    def sendPackets(self, level=0):
        sendBlock = """
for pkt in pkts:
    for outport in [self.port1, self.port2]:
        packet_out_msg = self.helper.build_packet_out(
            payload=str(pkt),
            metadata={
                "egress_port": outport,
                "_pad": 0
            })

        self.send_packet_out(packet_out_msg)
        testutils.verify_packet(self, pkt, outport)

    testutils.verify_no_other_packets(self)
"""
        return self.indentCode(sendBlock, level)

    def generateRunTestMethod(self, level=0):

        code_block = self.indentCode("def runTest(self):", level)
        code_block += self.assignVariable("pkts", "[]", level+1)

        for num, (socketId, addr) in enumerate(self.pubs.iteritems()):
            pktName = "pkt{}".format(num+1)
            code_block += self.createPacket(pktName, self.ips[socketId], self.broadcasts[addr], level+1)

        code_block += self.sendPackets(level+1)

        return code_block

    def generate(self):

        imports = [
            ("group", "ptf.testutils", ""),
            ("*", "lib.base_test", ""),
        ]

        if (self.mode == "test"):
            imports.append(("sys", "", ""))

        global_vars = []

        # merge the two dicts of ip addresses
        ips = self.pubs.copy()
        ips.update(self.subs)

        vars_from_mn = [
            ("ips", str(self.ips)),
        ]

        code = "#!/usr/bin/python"
        code += self.generateBlankLine()

        code += self.generatePreamble(imports, mode=self.mode)
        code += self.assignVariables(global_vars)

        code += self.addComment("The variables below are from the Mininet session")
        code += self.assignVariables(vars_from_mn)

        code += self.generateClassDefinition("FirstTest", "P4RuntimeTest")
        code += self.generateRunTestMethod(1)
        self.writeToFile(code)
