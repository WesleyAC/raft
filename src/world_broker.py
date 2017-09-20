"""
The main emulator of the world, and bootstrapper of tests.
"""

import unittest
import collections
from random import Random
from heapq import heappush, heappop


from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import sampled_from, just, integers, one_of
from hypothesis.strategies import fixed_dictionaries, sets, lists, permutations
import hypothesis.strategies

# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
from events import *
from node import Node
# from copy import deepcopy

# pylint: disable=too-many-instance-attributes
class WorldBroker(GenericStateMachine):
    "TODO"
    def __init__(self, log=None, catastrophy_level=0, ms_per_step=700, max_ms_per_event=400):
        # Run/Test Settings
        self.catastrophy_level = catastrophy_level
        self.time_window_length = ms_per_step
        self.event_window_length = max_ms_per_event
        self.message_send_delay = 6

        self.delays = []
        self.delay_index = 0
        self.leaders_history = collections.defaultdict(set)

        self.test_logging = log or []

        # Initialize the cluster
        self.node_ids = range(5)
        conf = {'election_timeout_window': (150, 300),
                'heartbeat_timeout': 50,
                'nodes': set(self.node_ids)}

        # Event Queue
        self.current_time = 0
        self.action_queue = []

        # File Management
        # Currently, we're modeling ideal, synchronous files system operations
        self.file_broker = {k: {} for k in self.node_ids}

        # Power Management
        self.power_broker = {'nodes': {k: Node(k, conf, Random(k), self) for k in self.node_ids},
                             'down_nodes': {}}

        # Time Management
        self.time_broker = {'node_time_offsets': {k: 0 for k in self.node_ids},
                            'node_timers': {k: None for k in self.node_ids}}

        # Network Management
        self.network_broker = {'connections':
                               set([(f, t) for f in self.node_ids
                                    for t in self.node_ids if t != f]),
                               'delays': {(f, t): 0 for f in self.node_ids
                                          for t in self.node_ids if t != f},
                               'duplicates': {(f, t): 0 for f in self.node_ids
                                              for t in self.node_ids if t != f}}

        # The nodes should be "Brought up" after all the brokers are in place
        for node in self.power_broker['nodes'].values():
            node.setup()

    def log(self, entry):
        "Updates a submitted entry with information about the current time, and appends it"
        entry['global_time'] = self.current_time
        self.test_logging.append(entry)

    def get_node_for_testing(self, node_id):
        '''Return the canonical version of a node given its node_id.
        For testing purposes only. This is required for verifying
        invariants because the node in 'nodes' can be a dummy
        DownNode which has no state and cannot be queried.'''

        return self.power_broker['down_nodes'].get(node_id, self.power_broker['nodes'][node_id])

    # Begin Helper functions for event generation
    def gen_basic_event(self, event_type, additional_map):
        "TODO"
        base_map = {'start_time': integers(min_value=self.current_time,
                                           max_value=self.time_window_length + self.current_time),
                    'event_length': integers(min_value=1, max_value=self.event_window_length)}
        base_map.update(additional_map)
        return fixed_dictionaries(base_map).flatmap(lambda x: just(event_type(x)))

    def gen_node(self):
        "TODO"
        return sampled_from(self.node_ids)

    def gen_node_set(self):
        "TODO"
        return sets(self.gen_node())

    def gen_node_pair(self):
        "TODO"
        return permutations(self.node_ids).flatmap(lambda x: just((x[0], x[1])))

    def gen_node_pairs(self):
        "TODO"
        return sets(self.gen_node_pair())

    # Begin Event Generators

    def gen_power_event(self):
        "TODO"
        return self.gen_basic_event(PowerDown, {'affected_node': self.gen_node()})

    def gen_clock_event(self):
        "TODO"
        return self.gen_basic_event(ClockSkew,
                                    {'affected_node': self.gen_node(),
                                     'skew_amount': integers(min_value=-100, max_value=100)})

    def gen_network_event(self):
        "TODO"
        return one_of(
            self.gen_basic_event(SendDelay,
                                 {'affected_nodes': self.gen_node_set(),
                                  'delay': integers(min_value=1,
                                                    max_value=self.event_window_length)}),
            self.gen_basic_event(SendDrop,
                                 {'affected_nodes': self.gen_node_set()}),
            self.gen_basic_event(ReceiveDrop,
                                 {'affected_nodes': self.gen_node_set(),
                                  'delay': integers(min_value=1,
                                                    max_value=self.event_window_length)}),
            self.gen_basic_event(TransmitDrop,
                                 {'affected_node_pair': self.gen_node_pair(),
                                  'delay': integers(min_value=1,
                                                    max_value=self.event_window_length)}),
            self.gen_basic_event(SendDuplicate,
                                 {'affected_node': (self.gen_node()),
                                  'delay': integers(min_value=1,
                                                    max_value=self.event_window_length)}))

    def gen_adverse_event(self):
        "TODO"
        return one_of(self.gen_network_event(), self.gen_power_event(), self.gen_clock_event())

    # Check that we have at most one leader per term.
    # Also, update leader_history.
    def check_leader_history(self):
        "TODO"
        for node_id in self.power_broker['nodes']:
            node = self.get_node_for_testing(node_id)
            if node.is_leader():
                self.leaders_history[node.term].add(node.node_id)
        for term in self.leaders_history:
            if not len(self.leaders_history[term]) <= 1:
                print(self.leaders_history)
                assert False

    def steps(self):
        "TODO"
        delays = lists(integers(1, self.message_send_delay))
        adverse_events = lists(self.gen_adverse_event(), max_size=self.catastrophy_level)
        randomness = {'delays': delays, 'adverse_events': adverse_events}
        return fixed_dictionaries(randomness)

    # pylint: disable=arguments-differ
    def execute_step(self, randomness):
        """
        steps is a list of steps (possibly len() 0)
        """

        # TODO: this seems like a bad way to get randomness.
        self.delays = randomness['delays']
        self.delay_index = 0

        # Add a set of events to the action_queue, an the corresponding events to heal it
        for event in randomness['adverse_events']:
            reversals = event.backout()
            heappush(self.action_queue, event)
            for rev in reversals:
                heappush(self.action_queue, rev)

        # Run the event loop
        run_until = self.current_time + self.time_window_length
        while self.current_time <= run_until:
            # Handle any event at the current slice in time

            while self.action_queue and self.action_queue[0].get_start_time() == self.current_time:
                self.dispatch_event(heappop(self.action_queue))
            # Trip timers if timer is past timeout.
            for node_id in self.node_ids:
                if self.time_broker['node_timers'][node_id]:
                    adjusted_time = self.current_time \
                                    + self.time_broker['node_time_offsets'][node_id]
                    if adjusted_time > self.time_broker['node_timers'][node_id]:
                        self.log({'event_type':'timer_trip', 'affected_node':node_id})
                        self.power_broker['nodes'][node_id].timer_trip()
            self.current_time += 1
            self.check_leader_history()



    def teardown(self):
        "TODO"
        if self.current_time > self.time_window_length / 2:
        # if self.current_time > self.time_window_length / 2:
            #-TODO: this check should be stronger.
            #-TODO: heal before checking for other catastrophy levels.
            if not self.leaders_history:
                assert False

    # Event Dispatch
    def dispatch_event(self, event):
        "TODO"
        self.log(event.event_map)
        if isinstance(event, NetworkEvent):
            event.handle(self.power_broker['nodes'], self.network_broker)
        elif isinstance(event, PowerEvent):
            if isinstance(event, PowerDown):
                # Special cross-broker concern, clear timer
                self.time_broker['node_timers'][event.event_map['affected_node']] = None
            event.handle(self.power_broker['nodes'], self.power_broker)
        elif isinstance(event, TimerEvent):
            event.handle(self.power_broker['nodes'], self.time_broker)

    # Handle Timer Events

    def set_timeout(self, node_id, timeout):
        "TODO"
        self.time_broker['node_timers'][node_id] = self.current_time + \
            self.time_broker['node_time_offsets'][node_id] + timeout

    def clear_timer(self, node_id):
        "TODO"
        self.time_broker['node_timers'][node_id] = None

    # Handle Network Events

    def send_to(self, origin, destination, data):
        "TODO"
        assert origin != destination

        delay = 1
        if self.delays:
            delay = self.delays[self.delay_index]
            self.delay_index = (self.delay_index + 1) % len(self.delays)

        event_time = self.current_time + delay + self.network_broker['delays'][(origin, destination)]
        event_map = {'affected_node': destination,
                     'start_time': event_time,
                     'data': data,
                     'sender': origin}

        heappush(self.action_queue, DeliverMessage(event_map))

# pylint: disable=invalid-name
TestSet = WorldBroker.TestCase

if __name__ == '__main__':
    unittest.main()
