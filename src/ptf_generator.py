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

    def create_networks(self, addrs):
        curr_network = self.NETWORK_SEED
        for addr in addrs:
            network = ipaddress.ip_network((curr_network, self.SUBNET_MASK))
            print(network.hosts())
            self.networks[addr] = (network, 0)
            curr_network += self.NETWORK_SIZE

    def add_host_to_network(self, socketId):
        socketState = self.socketStates[socketId]
        addr = socketState.addr
        (ip_network_addr, num_hosts) = self.networks[addr]
        ip_host_addr = ipaddress.ip_address(int(ip_network_addr.network_address) + num_hosts + 1)
        self.ips[socketId] = ip_host_addr
        self.networks[addr] = (ip_network_addr, num_hosts+1)

    def add_pubs(self, pubs):
        for pubId in pubs:
            self.add_host_to_network(pubId)

    def add_subs(self, subs):
        for subId in subs:
            self.add_host_to_network(subId)

    def __init__(self, fileName, mode, socketStates, addrs, pubs, subs, dataSends, dataRecvs):
        print(pubs)
        print(subs)
        PythonGenerator.__init__(self, fileName)
        self.mode = mode
        self.socketStates = socketStates
        self.dataSends = dataSends
        self.dataRecvs = dataRecvs
        self.create_networks(addrs)
        self.add_pubs(pubs)
        self.add_subs(subs)
        self.pubs = pubs
        self.subs = subs

    def createPacket(self, pktName, src, dst, level=0):
        pkt = """
print(\"Sending packet - {src} -> {dst}\")
{pktName} = testutils.simple_tcp_packet(
                        ip_src=str(ips[\"{src}\"]),
                        ip_dst=str(ips[\"{dst}\"]))
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

        for num, pubId in enumerate(self.pubs):
            pktName = "pkt{}".format(num+1)
            # network_addr = self.networks[self.socketStates[socketId].bindAddr][0]
            socketState = self.socketStates[pubId]
            addr = socketState.addr
            subs = filter(lambda subId: (self.socketStates[subId].addr == addr), self.subs)
            for sub in subs:
                code_block += self.createPacket(pktName, pubId, sub, level+1)



        code_block += self.sendPackets(level+1)

        return code_block

    def generate(self):

        imports = [
            ("group", "ptf.testutils", ""),
            ("*", "lib.base_test", ""),
            ('ipaddress', '', '')
        ]

        if (self.mode == "test"):
            imports.append(("sys", "", ""))

        global_vars = []

        # merge the two dicts of ip addresses
        foramtted_ips = dict((str(k), str(v)) for k,v in self.ips.items())

        vars_from_mn = [
            ("ips", str(foramtted_ips)),
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
