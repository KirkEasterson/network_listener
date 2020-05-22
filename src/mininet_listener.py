from abc import abstractmethod
from enum import Enum
import logging
from ptf_generator import ptfGenerator


class Observable:

    def __init__(self):
        self._observers = set()

    def register(self, observer):
        self._observers.add(observer)

    def unregister(self, observer):
        self._observers.remove(observer)

    def unregister_all(self, observer):
        self._observers.clear()

    def notify_observers(self, *args, **kwargs):
        for observer in self._observers:
            observer.notify(self, *args, **kwargs)


class Observer:

    def __init__(self, observable):
        observable.register(self)

    @abstractmethod
    def notify(self, *args, **kwargs):
        pass


class EventHandler(Observable):

    commands = []

    hosts = set()
    switches = set()
    controllers = set()
    links = set() # tuples containing the ends of a link (order is irrelevant)

    macs = {} # key:hostName ; value:MAC
    ips = {} # key:hostName ; value:IP

    pings = set() # tuples containing (src,dst)

    def __init__(self):
        Observable.__init__(self)
        logging.basicConfig(filename="mininet_listener.log", filemode="w",format="%(asctime)s %(message)s", level="INFO")

    def sessionStarted(self):
        logging.info("Session started")

    def sessionStopped(self):
        logging.info("Session stopped")
        generator = ptfGenerator("mininet_listener_ptf", self.commands, self.hosts, self.switches, self.controllers, self.links, self.macs, self.ips, self.pings)
        generator.generate()

    def hostAdded(self, host):
        # Host doesn't have a MAC address at this point, but they an IP
        self.hosts.add(host.name)
        self.ips[host.name]= host.params["ip"]
        logging.info("New host created:{} {}".format(host, host.params["ip"]))

    def hostDeleted(self, host):
        self.hosts.discard(host.name)
        logging.info("Host deleted: {} {}".format(host, host.params))

    def switchAdded(self, switch):
        self.switches.add(switch.name)
        logging.info("New switch created\t{}{}".format(switch, switch.params))

    def switchDeleted(self, switch):
        self.switches.discard(switch.name)
        logging.info("Switch deleted")

    def controllerAdded(self, controller):
        self.controllers.add(controller.name)
        logging.info("New controller created\t{}{}".format(controller, controller.params))

    def controllerDeleted(self, controller):
        self.controllers.discard(controller.name)
        logging.info("Controller deleted\t{}{}".format(controller, controller.params))

    def natAdded(self, nat):
        self.notify_observers("New NAT added", nat)

    def linkAdded(self, link):
        self.links.add((link.intf1, link.intf2))
        logging.info("Link added from {} to {}".format(link.intf1, link.intf2))

    def linkDeleted(self, link):
        self.links.discard((link.intf1, link.intf2))
        logging.info("Link deleted from {} to {}".format(link.intf1, link.intf2))

    def hostsConfigured(self, hosts):
        logging.info("Hosts configured {}".format(hosts))

    def pingSent(self, src, dst):
        self.commands.append(("Ping", src, dst))
        self.macs[src.name]=src.MAC()
        self.macs[dst.name]=dst.MAC()
        self.pings.add((src.name,dst.name))
        logging.info("Ping sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.MAC(), dst, dst.MAC()))

    def pingFullSent(self, src, dst):
        self.commands.append(("Ping full", src, dst))
        logging.info("Ping full sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))

    def pingAllSent(self, timeout):
        self.commands.append(("Ping all", timeout))
        logging.info("Ping all sent with timeout {}".format(timeout))

    def pingPairSent(self, src, dst):
        self.commands.append(("Ping pair", src, dst))
        logging.info("Ping pair sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))

    def pingAllFullSent(self, src):
        self.commands.append(("Ping all full", src))
        logging.info("Ping all full sent from {}\t{}{}".format(src, src, src.params))

    def pingPairFullSent(self, src, dst):
        self.commands.append(("Ping pair full", src, dst))
        logging.info("Ping pair full sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))

    def linkStatusConfigured(self, src, dst, status):
        logging.info("Link status configured to {}\t{}{}\t{}{}".format(status, src, dst, src,  src.params, dst, dst.params))


class EventListener(Observer):

    def __init__(self, observable):
        Observer.__init__(self, observable)

    def notify(self, *args, **kwargs):
        pass