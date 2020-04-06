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
    HOST_CREATED = "New host created"


class EventHandler(Observable):

    filename = ""

    def __init__(self):
        Observable.__init__(self)

    def create_event(self, event_type, info):
        self.notify_observers(event_type,info.params,info.intfs,info.ports,info.nameToIntf)


class EventListener(Observer):

    filename = ""

    def __init__(self, observable, filename):
        self.filename = filename
        Observer.__init__(self, observable)

    def notify(self, *args, **kwargs):
        with open(self.filename, 'a') as out_file:
            for arg in args:
                out_file.write(str(arg)+"\n")
