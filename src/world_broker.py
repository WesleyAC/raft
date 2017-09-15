import unittest

from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples,sampled_from,just,integers,one_of,fixed_dictionaries,sets,lists

from random import Random
from heapq import heapify,heappush,heappop
from events import *
from node import Node
from copy import copy


class WorldBroker(GenericStateMachine):
    def __init__(self):
        # Run/Test Settings
        self.catastrophy_level = 0
        self.time_window_length = 400
        self.event_window_length = 150
        self.message_send_delay = 6

        # Initialize the cluster
        self.node_ids = range(5)
        conf = {'heartbeat_window': (150,300),'nodes':set(self.node_ids)}

        # Event Queue
        self.current_time = 0
        self.action_queue = []


        # File Management
        # Currently, we're modeling ideal, synchronous files system operations
        self.file_broker = {k:{} for k in self.node_ids}


        # Power Management
        self.power_broker = {'up_nodes': {k:Node(k,conf,Random(k),self) for k in self.node_ids},
                             'down_nodes': {}}

        # Time Management
        self.time_broker = {'node_time_offsets': {k:0 for k in self.node_ids},
                            'node_timers': {k:None for k in self.node_ids}}

        # Network Management
        self.network_broker = {'connections':set([(f,t) for f in self.node_ids for t in self.node_ids if t != f]),
                               'delays':{(f,t):0 for f in self.node_ids for t in self.node_ids if t != f},
                               'duplicates':{(f,t):0 for f in self.node_ids for t in self.node_ids if t != f}
        }

        # The nodes should be "Brough up" after all the brokers are in place
        for node in self.power_broker['up_nodes'].values():
            node.setup()


    # Begin Helper functions for event generation
    def gen_basic_event(self,event_type,additional_map):
        base_map = {'start_time': integers(min_value=self.current_time,
                                           max_value=self.event_window_length+self.current_time),
                    'event_length': integers(min_value=1,max_value=self.event_window_length)}
        base_map.update(additional_map)
        return fixed_dictionaries(base_map).flatmap(event_type)

    def gen_node(self):
        return sampled_from(self.node_ids)

    def gen_node_set(self):
        return sets(self.gen_node())

    def gen_node_pair(self):
        return tuple((self.gen_node(),self.gen_node()))

    def gen_node_pairs(self):
        return sets(self.gen_node_pair())


    # Begin Event Generators

    def gen_power_event(self):
        return self.gen_basic_event(PowerDown, {'affected_node':self.gen_node()})

    def gen_clock_event(self):
        return self.gen_basic_event(ClockSkew,
                                {'affected_node':self.gen_node(),
                                 'skew_amount':integers(min_value=-100,max_value=100)})

    def gen_network_event(self):
        return one_of(
            self.gen_basic_event(DeliveryDelay,
                             {'affected_nodes': self.gen_node_set(),
                              'delay':integers(min_value=1,max_value=self.time_window_length)}),
            self.gen_basic_event(DeliveryDrop,
                             {'affected_nodes': self.gen_node_set()}),
            self.gen_basic_event(ReceiveDrop,
                             {'affected_nodes': self.gen_node_set(),
                              'delay':integers(min_value=1,max_value=self.time_window_length)}),
            self.gen_basic_event(TransmitDrop,
                             {'affected_node_pair': self.gen_node_pair(),
                              'delay':integers(min_value=1,max_value=self.time_window_length)}),
            self.gen_basic_event(DeliveryDuplicate,
                             {'affected_node': (self.gen_node()),
                              'delay':integers(min_value=1,max_value=self.time_window_length)}))

    def gen_adverse_event(self):
        return one_of(self.gen_network_event(),self.gen_power_event(),self.gen_clock_event())


    def steps(self):
        return lists(self.gen_adverse_event(),max_size=self.catastrophy_level)

    def execute_step(self, steps):
        """
        steps is a list of steps (possibly len() 0)
        """

        # Add a set of events to the action_queue, an the corresponding events to heal it
        for event in steps:
            reversals = event.reverse()
            heappush(self.action_queue,event.prioritize())
            for rev in reversals:
                heappush(self.action_queue,rev.prioritize())

        # Run the event loop
        run_until = self.current_time + self.time_window_length
        while self.current_time <= run_until:
            # Handle any event at the current slice in time

            while len(self.action_queue) > 0 and self.action_queue[0][0] == self.current_time:
                self.dispatch_event(self.action_queue.pop())
            # Trip timers if we're there
            for node in self.node_ids:
                if self.time_broker['node_timers'][node] and self.current_time + self.time_broker['node_time_offsets'][node] > self.time_broker['node_timers'][node]:
                    self.power_broker['up_nodes'][node].timer_trip()
            self.current_time += 1


    # Event Dispatch
    def dispatch_event(self,event):
        if isinstance(event,NetworkEvent):
            event.handle(self.power_broker['up_nodes'],self.network_broker)
        elif isinstance(event,PowerEvent):
            if isinstance(event,PowerDown):
                # Special cross-broker concern, clear timer
                self.time_broker['node_timers'][event['affected_node']] = None
            event.handle(self.power_broker['up_nodes'],self.power_broker)
        elif isinstance(event,TimerEvent):
            event.handle(self.power_broker['up_nodes'],self.time_broker)

    # Handle Timer Events

    def set_timeout(self,node_id,timeout):
        self.time_broker['node_timers'][node_id] = self.current_time + self.time_broker['node_time_offsets'][node_id] + timeout

    def clear_timer(self,node_id):
        self.time_broker['node_timers'][node_id] = None

    # Handle Network Events

    def send_to(self,sender,to,data):
        heappush(self.action_queue,DeliverMessage({'affected_node':to,'start_time':self.current_time + self.message_send_delay, 'data': data, 'sender': sender}))

TestSet = WorldBroker.TestCase

if __name__ == '__main__':
    unittest.main()
