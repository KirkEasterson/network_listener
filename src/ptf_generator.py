import os

class PythonGenerator:

    fileName = ""

    def __init__(self, fileName):
        self.fileName = fileName


    def writeToFile(self, code):
        file = open(self.fileName, "w")
        file.write(code)
        file.close()


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
        importLine = "{}import {}{}".format(fromPortion, importValue, asPortion)
        return self.indentCode(importLine, level)


    # imports is an array of tuples containing (importValue, fromvalue, asValue)
    # this doesn't read like a usual python import, but makes it easy to allow for
    #   optional "from ..." and "... as ..." values
    def generatePreamble(self, imports, level=0):
        preamble = ""
        for (importValue, fromValue, asValue) in imports:
            preamble += self.generateImport(importValue, fromValue, asValue)
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

    commands = ()
    hosts = set()
    switches = set()
    controllers = set()
    links = set()

    macs = {}
    ips = {}
    pings = {}

    def __init__(self, fileName, commands, hosts, switches, controllers, links, macs, ips, pings):
        PythonGenerator.__init__(self, fileName)
        self.commands = commands
        self.hosts = hosts
        self.switches = switches
        self.controllers = controllers
        self.links = links
        self.macs = macs
        self.ips = ips
        self.pings = pings

        pkts = []



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

        for num, (src, dst) in enumerate(self.pings, start=1):
            pktName = "pkt{}".format(num)
            code_block += self.createPacket(pktName, src, dst, level+1)

        code_block += self.sendPackets(level+1)

        return code_block



    def generate(self):

        imports = [
            ("group", "ptf.testutils", ""),
            ("*", "lib.base_test", ""),
        ]

        global_vars = []

        vars_from_mn = [
            ("hosts", str(self.hosts)),
            ("macs", str(self.macs)),
            ("ips", str(self.ips))
        ]

        code = self.generatePreamble(imports)
        code += self.assignVariables(global_vars)

        code += self.addComment("The variables below are from the Mininet session")
        code += self.assignVariables(vars_from_mn)
        
        code += self.generateClassDefinition("FirstTest", "P4RuntimeTest")
        code += self.generateRunTestMethod(1)
        self.writeToFile(code)
