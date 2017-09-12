from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers,one_of

from broker import timer,file_system,network,power

from random import Random

from node import Node

class MetaBroker(GenericStateMachine):
    def __init__(self):
        """
        The MetaBroker is in charge of setting up, testing, and coordinating work between
        nodes and their co/effects.

        For now, this is where cluster initialization happens.
        """
        conf = {'node_list':set(range(5)),'heartbeat_freq':100,'election_timeout_window':(150,300)}

        self.nodes = {}
        for nid in range(5):
            random_seed = Random()
            random_seed.seed(nid)
            self.nodes[nid] = Node(nid,conf,random_seed,self)

        self.action_queue = []
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


    # From File Broker
    def read_file(self,node_id,file_name):
        self.file_broker.read_file(node_id,file_name)

    def write_file(self,node_id,file_name,data):
        self.file_broker.write_file(node_id,file_name,data)


    # From Timer Broker
    def add_timer(self,node_id,time_out):
        self.timer_broker.add_timer(node_id,time_out)


    # From Network Broker
    def send_to(self,sender,to,data):
        self.network_broker.send_to(sender,to,data)
