import uuid

"""Mininet Listener

This file is contains code for creating a listener in Mininet(https://github.com/mininet/mininet). A modified version of
Mininet is in development that implements this listener (https://github.com/KirkEasterson/mininet). This implementation
uses an observer pattern with callback functions designed to be added at points in Mininet. These functions store the data
necessary to simulate the session in PTF (https://github.com/p4lang/ptf) and then perform tests from the Mininet session.
"""

from abc import abstractmethod
from enum import Enum
import logging
from ptf_generator import PtfGenerator


class Observable:
    """
    A class implementing an Observable from the Observer design pattern (https://en.wikipedia.org/wiki/Observer_pattern)

    ...

    Methods
    -------
    register(observer)
        Registers an observer to the Observable
    unregister(observer)
        Unregisters an observer from the Observable
    unregister_all()
        Unregisters all observers from the Observable
    notify_observers(*args, **kwargs)
        Notifies all observers
    """

    _obervers = None
    id = None

    def __init__(self):
        self._observers = set()
        self.id = uuid.uuid4()

    def register(self, observer):
        """
        Registers an observer to the Observable

        Parameters
        ----------
        observer : Observer
            The observe rot be registered
        """
        self._observers.add(observer)

    def unregister(self, observer):
        """
        Unregisters an observer from the Observable

        Parameters
        ----------
        observer : Observer
            The observe rot be unregistered
        """
        self._observers.remove(observer)

    def unregister_all(self):
        """
        Unregisters all observers from the Observable
        """
        self._observers.clear()

    def notify_observers(self, func, args):
        """
        Notifies all observers

        Parameters
        ----------
        *args : 
            Non-keyword arguments
        **kwargs : 
            Keyword arguments
        """
        for observer in self._observers:
            getattr(observer, func)(*args)


class Observer:
    """
    A class implementing an Observer from the Observer design pattern (https://en.wikipedia.org/wiki/Observer_pattern)

    ...

    Methods
    -------
    notify(*args, **kwargs)
        The method to be called when the Observer is notified from the Observable
    """

    observables = {}  # key:observableId ; value:observer

    def __init__(self):
        pass

    def register(self, observable):
        observable.register(self)
        self.observables[observable.id] = observable

    def unregister(self, observable):
        observable.unregister(self)
        try:
            del self.observables[observable.id]
        except KeyError as ex:
            print("No such key: '%s'" % ex.message)

    @abstractmethod
    def notify(self, id, *args, **kwargs):
        """
        The method to be called when the Observer is notified from the Observable

        Parameters
        ----------
        *args : 
            Non-keyword arguments
        **kwargs : 
            Keyword arguments
        """
        pass


class EventHandler(Observable):
    """
    This class is specific for callback functions in the Modified version of Mininet(https://github.com/KirkEasterson/mininet).
    It extends the Observable class, which implements an Observable from the Observer design pattern
    (https://en.wikipedia.org/wiki/Observer_pattern)

    ...

    Attributes
    ----------
    commands : str[]
        an array containing all commands issued in the Mininet session
    hosts : str[]
        an array containing all hostnames from the Mininet session
    switches : str[]
        an array containing all switches from the Mininet session
    controllers : str[]
        an array containing all controllers from the Mininet session
    links : (str,str)[]
        an array containing tuples of all links from the Mininet session. A link is from one host to another, and the order of the hosts is irrelevant
    macs : str{}
        a dict containing all MAC addresses from the Mininet session. The key is the host, and the value is the MAC address
    ips : str{}
        a dist containing all IP addresses from the Mininet session. The key is the host, and the value is the IP address
    pings : (str,str)[]
        an array containing tuples of pings from the Mininet session. They first item is the source and the second item is the destination

    Methods
    -------
    sessionStarted()
        Called at the beginning of the Mininet session
    sessionStopped()
        Called at the end of the Mininet session
    hostAdded(host)
        Callback function for when a host is added in the Mininet session
    hostDeleted(host)
        Callback function for when a host is deleted from the Mininet session
    switchAdded(switch)
        Callback function for when a switch is added in the Mininet session
    switchDeleted(switch)
        Callback function for when a switch is deleted from the Mininet session
    controllerAdded(host)
        Callback function for when a controller is added in the Mininet session
    controllerDeleted(host)
        Callback function for when a controller is deleted from the Mininet session
    natAdded(host)
        Callback function for when a NAT is added in the Mininet session
    linkAdded(link)
        Callback function for when a link is added in the Mininet session
    linkDeleted(link)
        Callback function for when a link is deleted from the Mininet session
    hostsConfigured(hosts)
        Callback function for when hosts have been configured in the Mininet session
    pingSent(src, dst)
        Callback function for when a ping is sent in the Mininet session
    pingFullSent(src, dst)
        Callback function for when a ping full is sent in the Mininet session
    pingAllSent(timeout)
        Callback function for when a ping all is sent in the Mininet session
    pingPairSent(src, dst)
        Callback function for when a ping pair is sent in the Mininet session
    pingAllFullSent(src)
        Callback function for when a ping all full is sent in the Mininet session
    pingPairFullSent(src, dst)
        Callback function for when a ping full sent is sent in the Mininet session
    linkStatusConfigured(src, dst, status)
        Callback function for when a link status is configured in the Mininet session.
    """

    commands = []

    hosts = []
    switches = []
    controllers = []
    links = []  # tuples containing the ends of a link (order is irrelevant)

    macs = {}  # key:hostName ; value:MAC
    ips = {}  # key:hostName ; value:IP

    pings = []  # tuples containing (src,dst)

    def __init__(self):
        Observable.__init__(self)

    def sessionStarted(self):
        """Called at the beginning of the Mininet session

        All this does is log that the session has started
        """
        logging.info("Session started")

    def sessionStopped(self):
        """Called at the end of the Mininet session

        This logs that the session has ended, and it also creates the PTF generator and generates the code.
        """
        logging.info("Session stopped")
        ptfGenerator = PtfGenerator("mininet_listener_ptf.py", self.commands, self.hosts,
                                    self.switches, self.controllers, self.links, self.macs, self.ips, self.pings)
        ptfGenerator.generate()

    def hostAdded(self, host):
        """Callback function for when a host is added in the Mininet session

        This adds the switch to the datastructure. It adds the hostname and IP address to the data structures.
        The host doesn't have a MAC address yet though, this is added to the data structure in a different callback

        Parameters
        ----------
        host : Host
            The host added in the Mininet session
        """
        self.hosts.append(host.name)
        self.ips[host.name] = host.params["ip"]
        logging.info("New host created: {} {}".format(host, host.params["ip"]))

    def hostDeleted(self, host):
        """Callback function for when a host is deleted from the Mininet session

        This removes the host from the data structure.

        Parameters
        ----------
        host : Host
            The host deleted from the Mininet session
        """
        self.hosts.remove(host.name)
        logging.info("Host deleted: {} {}".format(host, host.params))

    def switchAdded(self, switch):
        """Callback function for when a switch is added in the Mininet session

        This adds the switch to the datastructure

        Parameters
        ----------
        switch : Switch
            The switch added to the Mininet session
        """
        self.switches.append(switch.name)
        logging.info("New switch created\t{}{}".format(switch, switch.params))

    def switchDeleted(self, switch):
        """Callback function for when a switch is deleted from the Mininet session

        This removes the switch from the data structure.

        Parameters
        ----------
        switch : Switch
            The switch added o the Mininet session
        """
        self.switches.remove(switch.name)
        logging.info("Switch deleted")

    def controllerAdded(self, controller):
        """Callback function for when a controller is added in the Mininet session

        This adds the controller to the datastructure

        Parameters
        ----------
        controller : Controller
            The controller added to the Mininet session
        """
        self.controllers.append(controller.name)
        logging.info("New controller created\t{}{}".format(
            controller, controller.params))

    def controllerDeleted(self, controller):
        """Callback function for when a controller is deleted from the Mininet session

        This removes the controller from the data structure.

        Parameters
        ----------
        controller : Controller
            The controller deleted from the Mininet session
        """
        self.controllers.remove(controller.name)
        logging.info("Controller deleted\t{}{}".format(
            controller, controller.params))

    def natAdded(self, nat):
        """Callback function for when a NAT is added in the Mininet session

        Parameters
        ----------
        nat : MAT
            The nat added to the Mininet session
        """
        self.notify_observers("New NAT added", nat)

    def linkAdded(self, link):
        """Callback function for when a link is added in the Mininet session

        This adds the link to the datastructure

        Parameters
        ----------
        link : Link
            The link added to the Mininet session
        """
        self.links.append((link.intf1, link.intf2))
        logging.info("Link added from {} to {}".format(link.intf1, link.intf2))

    def linkDeleted(self, link):
        """Callback function for when a link is deleted from the Mininet session

        This removes the link from the data structure.

        Parameters
        ----------
        link : Link
            The link deleted from the Mininet session
        """
        self.links.remove((link.intf1, link.intf2))
        logging.info("Link deleted from {} to {}".format(
            link.intf1, link.intf2))

    def hostsConfigured(self, hosts):
        """Callback function for when hosts have been configured in the Mininet session

        Parameters
        ----------
        host : Host[]
            The hosts configured in the Mininet session
        """
        logging.info("Hosts configured {}".format(hosts))

    def pingSent(self, src, dst):
        """Callback function for when a ping is sent in the Mininet session

        This adds the ping to the datastructure, and also to the commands datastructure. The host receives a MAC address at this time, so
        the MAC address is also added to the datastructure.

        Parameters
        ----------
        src : Host
            The host that sent the ping in the Mininet session
        dst : Host
            The host that was pinged in the Mininet session
        """
        self.commands.append(("Ping", src, dst))
        self.macs[src.name] = src.MAC()
        self.macs[dst.name] = dst.MAC()
        self.pings.append((src.name, dst.name))
        logging.info("Ping sent from {} to {}\t{}{}\t{}{}".format(
            src, dst, src,  src.MAC(), dst, dst.MAC()))

    def pingFullSent(self, src, dst):
        """Callback function for when a ping full is sent in the Mininet session

        This adds the ping full to the commands datastructure.Callback function for when a ping full is sent in the Mininet session. This adds the
        ping full to the commands datastructure.

        Parameters
        ----------
        src : Host
            The host that sent the ping full in the Mininet session
        dst : Host
            The host that was ping fulled in the Mininet session
        """
        self.commands.append(("Ping full", src, dst))
        logging.info("Ping full sent from {} to {}\t{}{}\t{}{}".format(
            src, dst, src,  src.params, dst, dst.params))

    def pingAllSent(self, timeout):
        """Callback function for when a ping all is sent in the Mininet session

        This adds the ping all to the commands datastructure.

        Parameters
        ----------
        timeout : int
            The for the ping all sent in the Mininet session
        """
        self.commands.append(("Ping all", timeout))
        logging.info("Ping all sent with timeout {}".format(timeout))

    def pingPairSent(self, src, dst):
        """Callback function for when a ping pair is sent in the Mininet session

        This adds the ping pair to the commands datastructure.

        Parameters
        ----------
        src : Host
            The host that sent the ping pair in the Mininet session
        dst : Host
            The host that was ping paired in the Mininet session
        """
        self.commands.append(("Ping pair", src, dst))
        logging.info("Ping pair sent from {} to {}\t{}{}\t{}{}".format(
            src, dst, src,  src.params, dst, dst.params))

    def pingAllFullSent(self, src):
        """Callback function for when a ping all full is sent in the Mininet session

        This adds the ping all full to the commands datastructure.

        Parameters
        ----------
        src : Host
            The host that sent the ping all full in the Mininet session
        """
        self.commands.append(("Ping all full", src))
        logging.info("Ping all full sent from {}\t{}{}".format(
            src, src, src.params))

    def pingPairFullSent(self, src, dst):
        """Callback function for when a ping full sent is sent in the Mininet session

        This adds the ping full sent to the commands datastructure.

        Parameters
        ----------
        src : Host
            The host that sent the ping pair full in the Mininet session
        dst : Host
            The host that was ping pair fulled in the Mininet session
        """
        self.commands.append(("Ping pair full", src, dst))
        logging.info("Ping pair full sent from {} to {}\t{}{}\t{}{}".format(
            src, dst, src,  src.params, dst, dst.params))

    def linkStatusConfigured(self, src, dst, status):
        """Callback function for when a link status is configured in the Mininet session.

        Parameters
        ----------
        src : Host
            The host that sent the ping pair full in the Mininet session
        dst : Host
            The host that was ping pair fulled in the Mininet session
        status : str
            The status of the link that was configured
        """
        logging.info("Link status configured to {}\t{}{}\t{}{}".format(
            status, src, dst, src,  src.params, dst, dst.params))

    def socketAdded(self, domain, protocol):
        self.notify_observers("socketAdded", (self.id, domain, protocol))

    def socketClosed(self):
        self.notify_observers("socketClosed", (self.id,))

    def socketBinded(self, addr):
        self.notify_observers("socketBinded", (self.id, addr))

    def socketConnected(self, addr):
        self.notify_observers("socketConnected", (self.id, addr))

    def sockoptSet(self, level, option, value):
        self.notify_observers("sockoptSet", (self.id, level, option, value))

    def dataSent(self, data, flags):
        self.notify_observers("dataSent", (self.id, data, flags))

    def dataRecv(self, flags):
        self.notify_observers("dataRecv", (self.id, flags))


class EventListener(Observer):
    """
    This class is specific for callback functions in the Modified version of Mininet(https://github.com/KirkEasterson/mininet).
    It extends the Observer class, which implements an Observer from the Observer design pattern
    (https://en.wikipedia.org/wiki/Observer_pattern)

    ...

    Methods
    -------
    notify(*args, **kwargs)
        The method to be called when the EventListener is notified from the Observable
    """

    socketIds = None
    domains = {}  # key:socketId ; value:domain
    protocols = {}  # key:socketId ; value:protocol
    bindAddrs = {}  # key:socketId ; value:address
    connectAddrs = {}  # key:socketId ; value:address
    sockoptLevel = {}  # key:socketId ; value:address
    sockoptOption = {}  # key:socketId ; value:address
    sockoptValue = {}  # key:socketId ; value:address

    dataSends = []
    dataRecvs = []

    def __init__(self):
        Observer.__init__(self)
        logging.basicConfig(filename="nnpy_listener.log", filemode="w",
                            format="%(asctime)s %(message)s", level="INFO")
        logging.info("Session started")
        self.socketIds = set()

    def generate_code(self):
        logging.info("Code generation sequence beginning.")
        ptfGenerator = PtfGenerator("nanomsg_ptf.py", self.domains, self.domains, self.protocols,
                        self.bindAddrs, self.connectAddrs, self.sockoptLevel, self.sockoptOption,
                        self.sockoptValue, self.dataSends, self.dataRecvs)
        ptfGenerator.generate()

    def socketAdded(self, id, domain, protocol):
        self.socketIds.add(id)
        self.domains[id] = domain
        self.protocols[id] = protocol
        logging.info("socket added: {} {} {}".format(id, domain, protocol))

    def socketClosed(self, id):
        self.socketIds.remove(id)
        self.domains.pop(id, None)
        self.protocols.pop(id, None)
        self.bindAddrs.pop(id, None)
        self.connectAddrs.pop(id, None)
        self.sockoptLevel.pop(id, None)
        self.sockoptOption.pop(id, None)
        self.sockoptValue.pop(id, None)
        logging.info("Socket closed: {}".format(id))

        if (len(self.socketIds) == 0):
            self.generate_code()

    def socketBinded(self, id, addr):
        self.bindAddrs[id] = addr
        logging.info("Socket binded: {} {}".format(id, addr))

    def socketConnected(self, id, addr):
        self.connectAddrs[id] = addr
        logging.info("Socket connected: {} {}".format(id, addr))

    def sockoptSet(self, id, level, option, value):
        self.sockoptLevel[id] = level
        self.sockoptOption[id] = option
        self.sockoptValue[id] = value
        logging.info("Socket opt set: {} {} {} {}".format(
            id, level, option, value))

    def dataSent(self, id, data, flags):
        self.dataSends.append((id, data, flags))
        logging.info("Data sent: {} {} {}".format(id, data, flags))

    def dataRecv(self, id, flags):
        self.dataSends.append((id, flags))
        logging.info("Data received: {} {}".format(id, flags))

    def notify(self, *args, **kwargs):
        """
        The method to be called when the EventListener is notified from the Observable

        Parameters
        ----------
        *args : 
            Non-keyword arguments
        **kwargs : 
            Keyword arguments
        """
        pass
