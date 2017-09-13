class DownNode:
    def receive(self,sender,message):
        pass

    def timer_trip(self):
        pass

    def loaded_file(self,file_name,data):
        pass

    def saved_file(self,file_name):
        pass


class Node:
    def __init__(self,node_id,conf,random_seed,broker):
        self.node_id = node_id
        self.conf = conf
        self.random_seed = random_seed
        self.broker = broker

        self.term = 0
        self.log = [] # list[tuple(term, entry)]
        self.commit_index = 0
        self.last_applied = 0
        self.voted_for = None
        self.node_type = "F"
        self.votes_received = set()

    def change_type(self, to):
        assert to == "F" or to == "C" or to == "L"
        self.node_type = to
        self.votes_received = set()

    def update_term(self, term):
        """
        If term is greater than the current term, update the term and make any
        other needed state changes.
        """
        if term > self.term:
            self.term = term
            self.change_type("F")
            self.voted_for = None

    def receive(self,sender,message):
        pass

    def timer_trip(self):
        pass

    def loaded_file(self,file_name,data):
        pass

    def saved_file(self,file_name):
        pass
