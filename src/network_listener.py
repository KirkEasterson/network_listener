import uuid

"""Network Listener

This file is contains code for creating a listener in nnpy(https://github.com/nanomsg/nnpy). A modified version of
nnpy is in development that implements this listener (https://github.com/KirkEasterson/nnpy). This implementation
uses an observer pattern with callback functions designed to be added at points in nnpy. These functions store the data
necessary to simulate the session in PTF (https://github.com/p4lang/ptf) and then perform tests from the nnpy session.
"""

from abc import abstractmethod
from enum import Enum
import logging
import nnpy
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
        """
        Registers an observable to the Observer

        Parameters
        ----------
        observable : Observable
            The observe rot be registered
        """
        observable.register(self)
        self.observables[observable.id] = observable

    def unregister(self, observable):
        """
        Unregisters an observable from the Observer

        Parameters
        ----------
        observable : Observable
            The observable to be unregistered
        """
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
    This class is specific for callback functions in the modified version of
    nnpy(https://github.com/KirkEasterson/nnpy/tree/generate-ptf-source-code). It extends
    the Observable class, which implements an Observable from the Observer design pattern
    (https://en.wikipedia.org/wiki/Observer_pattern).

    This implementation will suffer when scaled, since it requires each method call to be
    written twice (in both EventHandler and EventListener). Ideally a generic update_listeners
    method would be implemented. If more callback methods are to be added, this generic
    update_listeners method should be implemented.

    ...

    Methods
    -------
    sessionStarted()
        Called at the beginning of the nnpy session
    """



    def __init__(self):
        Observable.__init__(self)

    def sessionStarted(self):
        """Called at the beginning of the nnpy session

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


class ListenerMode(Enum):
    STD = 0
    TEST = 1

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

    addr = ''

    def __init__(self, socketId, domain, protocol):
        self.socketId = socketId
        self.domain = domain
        self.protocol = protocol
    
    def setAddr(self, addr):
        self.addr = addr

class EventListener(Observer):
    """
    This class is specific for callback functions in the Modified version of nnpy(https://github.com/KirkEasterson/nnpy).
    It extends the Observer class, which implements an Observer from the Observer design pattern
    (https://en.wikipedia.org/wiki/Observer_pattern)

    ...

    Methods
    -------
    notify(*args, **kwargs)
        The method to be called when the EventListener is notified from the Observable
    """

    mode = None

    socketStates = None
    activeSockets = 0

    addrs = set()

    pubs = {}
    subs = {}

    dataSends = []
    dataRecvs = []

    def __init__(self, mode="std"):
        Observer.__init__(self)
        logging.basicConfig(filename="nnpy_listener.log", filemode="w",
                            format="%(asctime)s %(message)s", level="INFO")
        logging.info("Session started")
        self.socketStates = {}
        self.mode = mode

    def generate_code(self):
        logging.info("Code generation sequence beginning.")
        ptfGenerator = PtfGenerator("nanomsg_ptf.py", self.mode, self.socketStates, self.addrs, self.pubs, self.subs, self.dataSends, self.dataRecvs)
        ptfGenerator.generate()

    def socketAdded(self, id, domain, protocol):
        socketState = SocketState(id, domain, protocol)
        self.activeSockets += 1
        self.socketStates[id] = socketState
        if(protocol == nnpy.SUB or protocol == nnpy.PUB):
            logging.info("socket added: {} {} {}".format(id, domain, protocol))
        else:
            logging.error("socket added with unsupported protocol: {} {} {}".format(id, domain, protocol))

    def close(self, id):
        self.socketStates[id].closed = True
        self.activeSockets -= 1
        logging.info("Socket closed: {}".format(id))

        if (self.activeSockets == 0):
            self.generate_code()

    def bind(self, id, addr):
        # self.socketStates[id].bindAddr = addr
        self.addrs.add(addr)
        self.pubs[id] = addr
        self.socketStates[id].setAddr(addr)
        logging.info("Socket binded: {} {}".format(id, addr))

    def connect(self, id, addr):
        self.addrs.add(addr)
        self.subs[id] = addr
        self.socketStates[id].setAddr(addr)
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
        self.dataRecvs.append((id, flags))
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
