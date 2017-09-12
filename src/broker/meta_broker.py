from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers,one_of
from collections import namedtuple

from broker import timer,file_system,network,power

class MetaBroker(GenericStateMachine):
    def __init__(self):
        self.action_queue = []
        self.nodes = {}
        self.timer_broker = timer.TimerBroker(self.nodes)
        self.file_broker = file_system.FileBroker(self.nodes)
        self.network_broker = network.NetworkBroker(self.nodes)
        self.power_broker = power.PowerBroker(self.nodes)

    def steps(self):
        return one_of(tuples(just('Timer'),  self.timer_broker.steps()),
                      tuples(just('File'),   self.file_broker.steps()),
                      tuples(just('Network'),self.network_broker.steps()),
                      tuples(just('Power'),  self.power_broker.steps()))

    def execute_step(self, step):
        broker,action = step
        if broker == 'Timer':
            self.timer_broker.execute_step(action)
        elif broker == 'File':
            self.file_broker.execute_step(action)
        elif broker == 'Network':
            self.network_broker.execute_step(action)
        elif broker == 'Power':
            self.power_broker.execute_step(action)
