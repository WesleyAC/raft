"""
The actual implementation of raft.
"""

import math
from message import AppendEntries, AppendEntriesResponse, RequestVote, RequestVoteResponse


class DownNode:
    """
    DownNode is a mock node, intended to interoperate with the powerbroker to
    represent a node that is powered down.
    It's methods simply pass
    """
    def receive(self, sender, message):
        "Downed nodes receive no messages"
        pass

    def timer_trip(self):
        "Downed Nodes have no timers"
        pass

# pylint: disable=too-many-instance-attributes
class Node:
    """
    The workhorse of this raft implementation.
    """
    def __init__(self, node_id, conf, rng, broker):
        self.node_id = node_id
        self.conf = conf
        self.rng = rng
        self.broker = broker

        self.term = 0
        self.log = []  # list[tuple(term, entry)]
        self.commit_index = 0
        self.last_applied = 0
        self.voted_for = None
        self.node_type = 'Follower'
        self.votes_received = set()
        self.election_timeout = self.calculate_election_timeout()


    def test_log(self, event):
        "This logs events for debugging purposes"
        assert 'event_type' in event
        event['originating_node'] = self.node_id
        event['current_term'] = self.term
        event['current_type'] = self.node_type

    def calculate_election_timeout(self):
        " TODO "
        return self.rng.randint(self.conf['election_timeout_window'][0],
                                self.conf['election_timeout_window'][1])

    def is_candidate(self):
        "TODO"
        return self.node_type == 'Candidate'

    def is_follower(self):
        "TODO"
        return self.node_type == 'Follower'

    def is_leader(self):
        "TODO"
        return self.node_type == 'Leader'

    def setup(self):
        "Emulates a node booting up"
        self.broker.set_timeout(self.node_id, self.election_timeout)

    def change_type(self, new_type):
        """
        Convert this node to a different type, and make any other needed state changes.
        """
        self.test_log({'event_type':'change_type', 'to':new_type})
        #-TODO always log instead of logging when different?
        if self.node_type != new_type:
            self.test_log({'to_type': new_type,
                           'event_type': 'change_type'})
        assert new_type == 'Follower' or new_type == 'Candidate' or new_type == 'Leader'
        if new_type == 'Leader':
            assert self.node_type != 'Follower'

        self.node_type = new_type
        if new_type == 'Follower' or new_type == 'Candidate':
            self.broker.set_timeout(self.node_id, self.election_timeout)
        elif new_type == 'Leader':
            self.broker.set_timeout(
                self.node_id, self.conf['heartbeat_timeout'])

    def update_term(self, term, new_candidate):
        """
        If term is greater than the current term, update the term and make any
        other needed state changes.

        We avoid resetting the node to 'Follower' if we're updating the term
        because the node is starting a new election.
        """
        self.test_log({'event_type':'update_term', 'new_term':term, 'new_candidate':new_candidate})
        if term > self.term:
            if not new_candidate:
                self.change_type('Follower')
            self.term = term
            self.votes_received = set()
            self.voted_for = None
            self.election_timeout = self.calculate_election_timeout()
            self.test_log({'event_type': 'update_term'})

    def receive(self, sender, message):
        "TODO"
        self.update_term(message.term, False)
        assert isinstance(message, (AppendEntries, RequestVote, AppendEntriesResponse,\
                          RequestVoteResponse))
        if isinstance(message, AppendEntries):
            if self.is_follower():
                self.broker.set_timeout(self.node_id, self.election_timeout)
            elif self.is_candidate() or self.is_leader():
                self.change_type('Follower')
            else:
                # This case will fire when we add cluster config changes.
                assert False
        elif isinstance(message, RequestVote):
            if message.term < self.term or self.voted_for is not None:
                self.broker.send_to(self.node_id, sender,
                                    RequestVoteResponse(self.term, False))
            else:
                self.broker.send_to(self.node_id, sender,
                                    RequestVoteResponse(self.term, True))
                self.voted_for = sender
                self.test_log({'event_type': 'cast_vote', 'voted_for': sender})
        elif isinstance(message, AppendEntriesResponse):
            pass
        elif isinstance(message, RequestVoteResponse):
            if message.vote_granted and self.is_candidate():
                self.votes_received.add(sender)
                if len(self.votes_received) > math.floor(len(self.conf['nodes']) / 2):
                    self.change_type('Leader')

    def timer_trip(self):
        "TODO"
        #-TODO: this if statement was added to fix a "compile error". This was not
        # thought through and may be wrong.
        last_logged_term = -1
        last_logged_entry = None
        if self.log:
            last_logged_term = self.log[-1][0]
            last_logged_entry = self.log[-1][1]

        if not self.is_leader():
            self.change_type('Candidate')
            self.update_term(self.term + 1, True)
            self.votes_received.add(self.node_id)
            self.voted_for = self.node_id
            self.test_log({"event_type": "cast_vote", "voted_for": self.node_id})
            for node in self.conf['nodes']:
                if self.node_id != node:
                    self.broker.send_to(self.node_id, node,
                                        RequestVote(self.term, self.node_id,
                                                    len(self.log), last_logged_term))
        else:
            for node in self.conf['nodes']:
                if self.node_id != node:
                    self.broker.send_to(self.node_id, node,
                                        AppendEntries(self.term, self.node_id,
                                                      len(self.log), last_logged_entry,
                                                      [], self.commit_index))
            self.broker.set_timeout(
                self.node_id, self.conf['heartbeat_timeout'])
