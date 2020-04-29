from abc import abstractmethod
from enum import Enum


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

    commands = ()

    hosts = set()
    switches = set()
    controllers = set()
    links = set()

    def __init__(self):
        Observable.__init__(self)

    def sessionStarted(self):
        self.notify_observers("Session started")

    def sessionStopped(self):
        self.notify_observers("Session stopped")

    def hostAdded(self, host):
        self.hosts.add(host)
        self.notify_observers("New host created", host)

    def hostDeleted(self, host):
        self.hosts.discard(host)
        self.notify_observers("Host deleted", host)

    def switchAdded(self, switch):
        self.switches.add(switch)
        self.notify_observers("New switch created", switch)

    def switchDeleted(self, switch):
        self.switches.discard(switch)
        self.notify_observers("Switch deleted", switch)

    def controllerAdded(self, controller):
        self.controllers.add(controller)
        self.notify_observers("New controller added", controller)

    def controllerDeleted(self, controller):
        self.controllers.discard(controller)
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
        self.notify_observers("Ping sent", src, dst)

    def pingFullSent(self, src, dst):
        self.notify_observers("Ping full sent", src, dst)

    def pingAllSent(self, timeout):
        self.notify_observers("Ping all sent", timeout)

    def pingPairSent(self, src, dst):
        self.notify_observers("Ping pair sent", src, dst)

    def pingAllFullSent(self, src):
        self.notify_observers("Ping all full sent", src)

    def pingPairFullSent(self, src, dst):
        self.notify_observers("Ping pair sent", src, dst)

    def linkStatusConfigured(self, src, dst, status):
        self.notify_observers("Link status configured", src, dst, status)


class EventListener(Observer):
    filename = ""

    def __init__(self, observable, filename):
        self.filename = filename
        Observer.__init__(self, observable)

    def notify(self, *args, **kwargs):
        with open(self.filename, 'a') as out_file:
            for arg in args:
                out_file.write(str(arg) + "\n")
