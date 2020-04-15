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


class MininetEvent(Enum):
    ADD_HOST = "New host created"
    DEL_HOST = "Host deleted"
    ADD_SWITCH = "New switch created"
    DEL_SWITCH = "Switch deleted"
    ADD_CONTROLLER = "New controller created"
    DEL_CONTROLLER = "Controller deleted"
    ADD_LINK = "New link created"
    DEL_LINK = "Link deleted"
    CONFIG_HOSTS = "Hosts configured"

class MininetCommand(Enum):
    CONFIG_HOSTS = "Hosts configured"
    PING = "Ping sent"
    PING_FULL = "Ping full sent"
    PING_ALL = "Ping all sent"
    PING_PAIR = "Ping pair sent"
    PING_ALL_FULL = "Ping all full sent"
    PING_PAIR_FULL = "Ping pair full sent"


class EventHandler(Observable):

    filename = ""

    def __init__(self):
        Observable.__init__(self)

    # This event will be rewritten. I plan on creating methods for each event type. The
    # params will be passed down to that method and the PTF code will be written there
    def create_event(self, event_type, info):
        self.notify_observers(event_type, str(info))
        # The below works for anything that is not a Link. There should be events for
        #   each type of event, and that will properly handle a Link. For now, the above
        #   generic method is used.
        # self.notify_observers(event_type,info.params,info.intfs,info.ports,info.nameToIntf)

    def create_command(self, command_type):
        self.notify_observers(command_type)

class EventListener(Observer):

    filename = ""

    def __init__(self, observable, filename):
        self.filename = filename
        Observer.__init__(self, observable)

    def notify(self, *args, **kwargs):
        with open(self.filename, 'a') as out_file:
            for arg in args:
                out_file.write(str(arg)+"\n")
