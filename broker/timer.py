from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers
from collections import namedtuple


class TimerBroker(GenericStateMachine):
    def __init__(self,nodes):
        self.timer_queue = []
        self.nodes = nodes

    def steps(self):
        if len(self.timer_queue) > 1:
            return one_of(tuples(just('Invoke')),
                          tuples(just('Delay',integers(min_value=1,
                                                       max_value=len(self.timer_queue)-2))))
        if len(self.timer_queue) == 1:
            return just(tuples(just('Invoke')))
        return just(None)

    def execute_step(self, step):
        """
        A timer may be Invoked or Delayed an arbitrary amount of time, but won't be dropped.
        """
        if step[0] == 'Invoke':
            self.dispatch_next_timer()
        elif step[0] == 'Delay':
            delay = step[1]
            timer_bumped = self.timer_queue.pop(0)
            self.timer_queue = self.timer_queue[0:-delay] + [timer_bumped] + self.timer_queue[-delay:]

    def dispatch_next_timer(self):
        next_timer = self.timer_queue.pop(0)
        if next_timer:
            node_id,timer_id,time_out = next_timer
            self.nodes[node_id].timer_trip()

    def add_timer(self,node_id,timer_id,time_out):
        """
        add_timer is the public interface for the TimerBroker. members in the cluster call this function, and when the timer trips,
        Their 'timer_trip' function will be called.
        """
        self.timer_queue.append((node_id,time_out))
