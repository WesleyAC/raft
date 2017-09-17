import unittest

from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples,sampled_from,just,integers,one_of,fixed_dictionaries,sets,lists,permutations

import collections
from random import Random
from heapq import heapify,heappush,heappop
from events import *
from node import Node
from copy import deepcopy

class WorldBroker(GenericStateMachine):
    def __init__(self):
        # Run/Test Settings
        self.catastrophy_level = 0
        self.time_window_length = 700
        self.event_window_length = 150
        self.message_send_delay = 6

        self.leaders_history = collections.defaultdict(set)

        # Initialize the cluster
        self.node_ids = range(5)
        conf = {'election_timeout_window': (150,300),
                'heartbeat_timeout': 50,
                'nodes':set(self.node_ids)}

        # Event Queue
        self.current_time = 0
        self.action_queue = []

        # File Management
        # Currently, we're modeling ideal, synchronous files system operations
        self.file_broker = {k:{} for k in self.node_ids}

        # Power Management
        self.power_broker = {'nodes': {k: Node(k, conf, Random(k), self) for k in self.node_ids},
                             'down_nodes': {}}

        # Time Management
        self.time_broker = {'node_time_offsets': {k:0 for k in self.node_ids},
                            'node_timers': {k:None for k in self.node_ids}}

        # Network Management
        self.network_broker = {'connections':set([(f,t) for f in self.node_ids for t in self.node_ids if t != f]),
                               'delays':{(f,t):0 for f in self.node_ids for t in self.node_ids if t != f},
                               'duplicates':{(f,t):0 for f in self.node_ids for t in self.node_ids if t != f}
        }

        # The nodes should be "Brought up" after all the brokers are in place
        for node in self.power_broker['nodes'].values():
            node.setup()


    def get_node_for_testing(self, node_id):
        '''Return the canonical version of a node given its node_id.
        For testing purposes only. This is required for verifying invariants because the node in 'nodes' can be a dummy
        DownNode which has no state and cannot be queried.'''

        return self.power_broker['down_nodes'].get(node_id,self.power_broker['nodes'][node_id])

    # Begin Helper functions for event generation
    def gen_basic_event(self,event_type,additional_map):
        base_map = {'start_time': integers(min_value=self.current_time,
                                           max_value=self.time_window_length+self.current_time),
                    'event_length': integers(min_value=1,max_value=self.time_window_length)}
        base_map.update(additional_map)
        return fixed_dictionaries(base_map).flatmap(lambda x : just(event_type(x)))

    def gen_node(self):
        return sampled_from(self.node_ids)

    def gen_node_set(self):
        return sets(self.gen_node())

    def gen_node_pair(self):
        return permutations(self.node_ids).flatmap(lambda x: just((x[0],x[1])))

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
                              'delay':integers(min_value=1,max_value=self.event_window_length)}),
            self.gen_basic_event(DeliveryDrop,
                             {'affected_nodes': self.gen_node_set()}),
            self.gen_basic_event(ReceiveDrop,
                             {'affected_nodes': self.gen_node_set(),
                              'delay':integers(min_value=1,max_value=self.event_window_length)}),
            self.gen_basic_event(TransmitDrop,
                             {'affected_node_pair': self.gen_node_pair(),
                              'delay':integers(min_value=1,max_value=self.event_window_length)}),
            self.gen_basic_event(DeliveryDuplicate,
                             {'affected_node': (self.gen_node()),
                              'delay':integers(min_value=1,max_value=self.event_window_length)}))

    def gen_adverse_event(self):
        return one_of(self.gen_network_event(),self.gen_power_event(),self.gen_clock_event())


    # Check that we have at most one leader per term.
    # Also, update leader_history.
    def check_leader_history(self):
        for node_id in self.power_broker['nodes']:
            node = self.get_node_for_testing(node_id)
            if node.is_leader():
                self.leaders_history[node.term].add(node.node_id)
        for term in self.leaders_history:
            assert(len(self.leaders_history[term]) <= 1)

    def steps(self):
        return lists(self.gen_adverse_event(),max_size=self.catastrophy_level)

    def execute_step(self, adverse_events):
        """
        steps is a list of steps (possibly len() 0)
        """

        # Add a set of events to the action_queue, an the corresponding events to heal it
        for event in adverse_events:
            reversals = event.backout()
            heappush(self.action_queue,event)
            for rev in reversals:
                heappush(self.action_queue,rev)

        # Run the event loop
        run_until = self.current_time + self.time_window_length
        while self.current_time <= run_until:
            # Handle any event at the current slice in time

            while len(self.action_queue) > 0 and self.action_queue[0].get_start_time() == self.current_time:
                self.dispatch_event(self.action_queue.pop())
            # Trip timers if timer is past timeout.
            for node in self.node_ids:
                if self.time_broker['node_timers'][node]:
                    if self.current_time + self.time_broker['node_time_offsets'][node] > self.time_broker['node_timers'][node]:
                        self.power_broker['nodes'][node].timer_trip()
            self.current_time += 1

        self.check_leader_history()

    def teardown(self):
        if self.catastrophy_level == 0 and self.current_time > self.time_window_length / 2:
            # self.execute_step(20)
            # TODO: this check should be stronger.
            # TODO: heal before checking for other catastrophy levels.
            assert(len(self.leaders_history) > 0)

    # Event Dispatch
    def dispatch_event(self,event):
        if isinstance(event,NetworkEvent):
            event.handle(self.power_broker['nodes'],self.network_broker)
        elif isinstance(event,PowerEvent):
            if isinstance(event,PowerDown):
                # Special cross-broker concern, clear timer
                self.time_broker['node_timers'][event.event_map['affected_node']] = None
            event.handle(self.power_broker['nodes'],self.power_broker)
        elif isinstance(event,TimerEvent):
            event.handle(self.power_broker['nodes'],self.time_broker)

    # Handle Timer Events

    def set_timeout(self,node_id,timeout):
        self.time_broker['node_timers'][node_id] = self.current_time + self.time_broker['node_time_offsets'][node_id] + timeout

    def clear_timer(self,node_id):
        self.time_broker['node_timers'][node_id] = None

    # Handle Network Events

    def send_to(self,sender,to,data):
        assert(sender != to)

        event_time = self.current_time + self.message_send_delay + self.network_broker['delays'][(sender, to)]
        event_map = {'affected_node':to,
                                 'start_time': event_time,
                                 'data': data,
                                 'sender': sender}

        heappush(self.action_queue, DeliverMessage(event_map))

TestSet = WorldBroker.TestCase

if __name__ == '__main__':
    unittest.main()
