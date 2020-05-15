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
    links = set()

    def __init__(self):
        Observable.__init__(self)
        logging.basicConfig(filename="mininet_listener.log", filemode="w",format="%(asctime)s %(message)s", level="INFO")

    def sessionStarted(self):
        logging.info("Session started")
        self.notify_observers("Session started")

    def sessionStopped(self):
        logging.info("Session stopped")
        self.notify_observers("Session stopped")
        generator = ptfGenerator("mininet_listener_ptf", self.commands, self.hosts, self.switches, self.controllers, self.links)
        generator.generate()

    def hostAdded(self, host):
        self.hosts.add(host)
        logging.info("New host created\t{}{}".format(host, host.params))
        self.notify_observers("New host created", host.params)

    def hostDeleted(self, host):
        self.hosts.discard(host)
        logging.info("Host deleted\t{}{}".format(host, host.params))
        self.notify_observers("Host deleted", host)

    def switchAdded(self, switch):
        self.switches.add(switch)
        logging.info("New switch created\t{}{}".format(switch, switch.params))
        self.notify_observers("New switch created", switch.params)

    def switchDeleted(self, switch):
        self.switches.discard(switch)
        logging.info("Switch deleted")
        self.notify_observers("Switch deleted\t{}{}".format(switch, switch.params))

    def controllerAdded(self, controller):
        self.controllers.add(controller)
        logging.info("New controller created\t{}{}".format(controller, controller.params))
        self.notify_observers("New controller added", controller)

    def controllerDeleted(self, controller):
        self.controllers.discard(controller)
        logging.info("Controller deleted\t{}{}".format(controller, controller.params))
        self.notify_observers("Controller deleted", controller)

    def natAdded(self, nat):
        self.notify_observers("New NAT added", nat)

    def linkAdded(self, link):
        self.links.add(link)
        self.notify_observers("New link added", link)

    def linkDeleted(self, link):
        self.links.discard(link)
        self.notify_observers("Link deleted", link)

    def hostsConfigured(self, hosts):
        self.notify_observers("Host configured", hosts)

    def pingSent(self, src, dst):
        self.commands.append(("Ping", src, dst))
        logging.info("Ping sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))
        self.notify_observers("Ping sent", src, dst)

    def pingFullSent(self, src, dst):
        self.commands.append(("Ping full", src, dst))
        logging.info("Ping full sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))
        self.notify_observers("Ping full sent", src, dst)

    def pingAllSent(self, timeout):
        self.commands.append(("Ping all", timeout))
        logging.info("Ping all sent with timeout {}".format(timeout))
        self.notify_observers("Ping all sent", timeout)

    def pingPairSent(self, src, dst):
        self.commands.append(("Ping pair", src, dst))
        logging.info("Ping pair sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))
        self.notify_observers("Ping pair sent", src, dst)

    def pingAllFullSent(self, src):
        self.commands.append(("Ping all full", src))
        logging.info("Ping all full sent from {}\t{}{}".format(src, src, src.params))
        self.notify_observers("Ping all full sent", src)

    def pingPairFullSent(self, src, dst):
        self.commands.append(("Ping pair full", src, dst))
        logging.info("Ping pair full sent from {} to {}\t{}{}\t{}{}".format(src, dst, src,  src.params, dst, dst.params))
        self.notify_observers("Ping pair sent", src, dst)

    def linkStatusConfigured(self, src, dst, status):
        self.notify_observers("Link status configured", src, dst, status)
        logging.info("Link status configured to {}\t{}{}\t{}{}".format(status, src, dst, src,  src.params, dst, dst.params))


class EventListener(Observer):

    def __init__(self, observable):
        Observer.__init__(self, observable)

    def notify(self, *args, **kwargs):
        pass