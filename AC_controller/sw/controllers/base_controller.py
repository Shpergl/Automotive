from helpers.observer import ControllerNotifier


class BaseStateSelector:
    def __init__(self, sequence, initial_state=None):
        self._sequence = sequence
        self._current_idx = 0
        if initial_state is not None:
            self.state = initial_state

    @property
    def state(self):
        return self._sequence[self._current_idx]

    @state.setter
    def state(self, value):
        if value in self._sequence:
            self._current_idx = self._sequence.index(value)
        else:
            print("Cannot set state: {}. Not in sequence: {}".format(value, self._sequence))


class CycledSelector(BaseStateSelector):

    def next_state(self):
        next_idx = self._current_idx + 1
        if next_idx > len(self._sequence) - 1:
            self._current_idx = 0
        else:
            self._current_idx = next_idx
        # self._current_state = self._sequence[self._current_idx]


class SequentialSelector(CycledSelector):
    def _check_next_idx(self, idx):
        return 0 <= idx <= len(self._sequence) - 1

    def next_state(self):
        next_idx = self._current_idx + 1
        print("FAN_SPEED next_idx: {}".format(next_idx))
        if self._check_next_idx(next_idx):
            self._current_idx = next_idx
            # self._current_state = self._sequence[self._current_idx]

    def prev_state(self):
        prev_idx = self._current_idx - 1
        print("FAN_SPEED prev_idx: {}".format(prev_idx))
        if self._check_next_idx(prev_idx):
            self._current_idx = prev_idx
            # self._current_state = self._sequence[self._current_idx]


class BaseController(ControllerNotifier):
    def __init__(self, controller_type):
        super(BaseController, self).__init__()
        self._controller_type = controller_type

    @property
    def controller_type(self):
        return self._controller_type

    def get_packed_data(self):
        pass

    def send_update(self):
        self.notify(self.controller_type, self)
