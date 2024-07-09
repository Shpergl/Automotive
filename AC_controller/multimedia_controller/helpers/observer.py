
class Observer:
    def subscribe(self, subject):
        if subject:
            subject.attach(self)

    def unsubscribe(self, subject):
        if subject:
            subject.detach(self)

    def update(self, subject_type, subject):
        pass


class Subject:
    def attach(self, observer):
        pass

    def detach(self, observer):
        pass

    def notify(self, subject_type, subject):
        pass


class ControllerNotifier(Subject):
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, subject_type, subject):
        for observer in self._observers:
            observer.update(subject_type, subject)
