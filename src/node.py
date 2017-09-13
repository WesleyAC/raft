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
        self.node_type = "F"
        self.votes_received = set()
        self.election_timout = self.calculate_election_timeout()

    def calculate_election_timeout(self):
        self.rng.rand_int(self.conf.election_timeout_window[0],
                          self.conf.election_timeout_window[1]))

    def setup(self):
        self.broker.add_timer(self.node_id, self.election_timeout)

    def change_type(self, to):
        """
        Convert this node to a different type, and make any other needed state changes.
        """
        assert to == "F" or to == "C" or to == "L"
        self.node_type = to
        if to == "F" or to == "C":
            self.broker.add_timer(self.node_id, self.election_timeout)
        elif to == "L":
            self.broker.add_timer(self.node_id, self.conf.heartbeat_freq)

    def update_term(self, term):
        """
        If term is greater than the current term, update the term and make any
        other needed state changes.
        """
        if term > self.term:
            self.term = term
            self.change_type("F")
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
            if self.node_type == "F":
                self.broker.add_timer(self.node_id, self.election_timeout)
            elif self.node_type == "C" or self.node_type == "L":
                self.change_type("F")
        elif type(message) == RequestVote:
            if message.term < self.term or self.voted_for is not None:
                self.broker.send_to(self.node_id, sender, RequstVoteResponse(self.term, False))
            else:
                self.broker.send_to(self.node_id, sender, RequstVoteResponse(self.term, True))
        elif type(message) == AppendEntriesResponse:
            pass
        elif type(message) == RequestVoteResponse:
            if message.vote_granted:
                self.votes_received.add(sender)
                if len(self.votes_received) > math.floor(len(self.conf.node_list)/2):
                    self.change_type("L")

    def timer_trip(self):
        if self.node_type == "F" or self.node_type == "C":
            self.change_type("C")
            self.update_term(self.term+1)
            self.votes_received.add(self.node_id)
            self.voted_for = self.node_id
            for node in self.conf.node_list:
                self.broker.send_to(self.node_id, node,
                    RequestVote(self.term, self.node_id, len(self.log), self.log[-1][0]))
        elif self.node_type == "L":
            for node in self.conf.node_list:
                self.broker.send_to(self.node_id, node,
                        AppendEntries(self.term, self.node_id, len(self.log), self.log[-1][1], [], self.commit_index))
