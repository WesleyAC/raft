from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers,one_of
from collections import namedtuple

from brokers import timer,file_system,network,power

class MetaBroker(GenericStateMachine):
    def __init__(self):
        self.action_queue = []
        self.nodes = {}
        self.timer_broker = timer.TimerBroker(nodes)
        self.file_broker = file_system.FileBroker(nodes)
        self.network_broker = network.NetworkBroker(nodes)
        self.power_broker = power.PowerBroker(nodes)

    def steps(self):
        return one_of(tuples(just('Timer',  self.timer_broker.step())),
                      tuples(just('File',   self.file_broker.step())),
                      tuples(just('Network',self.network_broker.step())),
                      tuples(just('Power',  self.power_broker.step())))

    def execute_step(self, step):
        broker,action = step[0]
        if broker == 'Timer':
            self.timer_broker.execute_step(action)
        elif broker == 'File':
            self.file_broker.execute_step(action)
        elif broker == 'Network':
            self.network_broker.execute_step(action)
        elif broker == 'Power':
            self.power_broker.execute_step(action)
