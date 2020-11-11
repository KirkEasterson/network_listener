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

    _obervers = {}
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

    def unregister_all(self):
        """
        Unregisters all observervables from the Observer
        """
        self.observables.clear()

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

    Methods
    -------
    sessionStarted()
        Called at the beginning of the Mininet session
    """

    def __init__(self):
        Observable.__init__(self)

    def sessionStarted(self):
        """Called at the beginning of the Mininet session

        All this does is log that the session has started
        """
        logging.info("Session started")

    def socketAdded(self, domain, protocol):
        self.notify_observers("socketAdded", (self.id, domain, protocol))

    def close(self):
        self.notify_observers("close", (self.id,))

    def bind(self, addr):
        self.notify_observers("bind", (self.id, addr))

    def connect(self, addr):
        self.notify_observers("connect", (self.id, addr))

    def setsockopt(self, level, option, value):
        self.notify_observers("setsockopt", (self.id, level, option, value))

    def send(self, data, flags):
        self.notify_observers("send", (self.id, data, flags))

    def recv(self, flags):
        self.notify_observers("recv", (self.id, flags))


class SocketState():

    socketId = None

    closed = False

    domain = None
    protocol = None
    bindAddr = None
    connectAddr = None
    sockoptLevel = None
    sockoptOption = None
    sockoptValue = None

    def __init__(self, socketId, domain, protocol):
        self.socketId = socketId
        self.domain = domain
        self.protocol = protocol

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

    socketStates = None
    activeSockets = 0

    dataSends = []
    dataRecvs = []

    def __init__(self):
        Observer.__init__(self)
        logging.basicConfig(filename="nnpy_listener.log", filemode="w",
                            format="%(asctime)s %(message)s", level="INFO")
        logging.info("Session started")
        self.socketStates = {}

    def generate_code(self):
        logging.info("Code generation sequence beginning.")
        ptfGenerator = PtfGenerator("nanomsg_ptf.py", self.socketStates, self.dataSends, self.dataRecvs)
        ptfGenerator.generate()

    def socketAdded(self, id, domain, protocol):
        socketState = SocketState(id, domain, protocol)
        self.activeSockets += 1
        self.socketStates[id] = socketState
        logging.info("socket added: {} {} {}".format(id, domain, protocol))

    def close(self, id):
        self.socketStates[id].closed = True
        self.activeSockets -= 1
        logging.info("Socket closed: {}".format(id))

        if (self.activeSockets == 0):
            self.generate_code()

    def bind(self, id, addr):
        self.socketStates[id].bindAddr = addr
        logging.info("Socket binded: {} {}".format(id, addr))

    def connect(self, id, addr):
        self.socketStates[id].connectAddrs = addr
        logging.info("Socket connected: {} {}".format(id, addr))

    def setsockopt(self, id, level, option, value):
        self.socketStates[id].sockoptLevel = level
        self.socketStates[id].sockoptOption = option
        self.socketStates[id].sockoptValue = value
        logging.info("Socket opt set: {} {} {} {}".format(
            id, level, option, value))

    def send(self, id, data, flags):
        self.dataSends.append((id, data, flags))
        logging.info("Data sent: {} {} {}".format(id, data, flags))

    def recv(self, id, flags):
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
