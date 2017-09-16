import math
from message import AppendEntries, AppendEntriesResponse, RequestVote, RequestVoteResponse


class DownNode:
    def receive(self,sender,message):
        pass

    def timer_trip(self):
        pass

class Node:
    def __init__(self,node_id,conf,rng,broker):
        self.node_id = node_id
        self.conf = conf
        self.rng = rng
        self.broker = broker

        self.term = 0
        self.log = [] # list[tuple(term, entry)]
        self.commit_index = 0
        self.last_applied = 0
        self.voted_for = None
        self.node_type = 'Follower'
        self.votes_received = set()
        self.election_timeout = self.calculate_election_timeout()

    def calculate_election_timeout(self):
        return self.rng.randint(self.conf['election_timeout_window'][0],
                                self.conf['election_timeout_window'][1])

    def is_candidate(self):
        return self.node_type == 'Candidate'

    def is_follower(self):
        return self.node_type == 'Follower'

    def is_leader(self):
        return self.node_type == 'Leader'

    def setup(self):
        self.broker.set_timeout(self.node_id, self.election_timeout)

    def change_type(self, to):
        """
        Convert this node to a different type, and make any other needed state changes.
        """
        print('change_type {}: {} -> {}'.format(self.node_id,self.node_type, to))

        assert to == 'Follower' or to == 'Candidate' or to == 'Leader'
        self.node_type = to
        if to == 'Follower' or to == 'Candidate':
            self.broker.set_timeout(self.node_id, self.election_timeout)
        elif to == 'Leader':
            self.broker.set_timeout(self.node_id, self.conf['heartbeat_timeout'])

    def update_term(self, term):
        """
        If term is greater than the current term, update the term and make any
        other needed state changes.
        """
        if term > self.term:
            self.term = term
            self.change_type('Follower')
            self.votes_received = set()
            self.voted_for = None
            self.election_timout = self.calculate_election_timeout()

    def receive(self,sender,message):
        self.update_term(message.term)
        assert type(message) == AppendEntries or \
               type(message) == RequestVote or \
               type(message) == AppendEntriesResponse or \
               type(message) == RequestVoteResponse
        if type(message) == AppendEntries:
            if self.is_follower():
                self.broker.set_timeout(self.node_id, self.election_timeout)
            elif self.is_candidate() or self.is_leader():
                self.change_type('Follower')
            else:
                # This case will fire when we add cluster config changes.
                assert(False)
        elif type(message) == RequestVote:
            if message.term < self.term or self.voted_for is not None:
                self.broker.send_to(self.node_id, sender, RequestVoteResponse(self.term, False))
            else:
                self.broker.send_to(self.node_id, sender, RequestVoteResponse(self.term, True))
        elif type(message) == AppendEntriesResponse:
            pass
        elif type(message) == RequestVoteResponse:
            if message.vote_granted:
                self.votes_received.add(sender)
                if len(self.votes_received) > math.floor(len(self.conf['nodes'])/2):
                    self.change_type('Leader')

    def timer_trip(self):
        # TODO: this if statement was added to fix a "compile error". This was not thought through and may be
        # wrong.
        print('timer_trip {}'.format(self.node_id))

        last_logged_term = -1
        last_logged_entry = None
        if len(self.log) > 0:
            last_logged_term = self.log[-1][0]
            last_logged_entry = self.log[-1][1]

        if not self.is_leader():
            self.change_type('Candidate')
            self.update_term(self.term+1)
            self.votes_received.add(self.node_id)
            self.voted_for = self.node_id
            for node in self.conf['nodes']:
                if self.node_id != node:
                    self.broker.send_to(self.node_id, node,
                        RequestVote(self.term, self.node_id, len(self.log), last_logged_term))
        else:
            for node in self.conf['nodes']:
                if self.node_id != node:
                    self.broker.send_to(self.node_id, node,
                        AppendEntries(self.term, self.node_id, len(self.log), last_logged_entry, [], self.commit_index))
            self.broker.set_timeout(self.node_id, self.conf['heartbeat_timeout'])
