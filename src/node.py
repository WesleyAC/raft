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
        self.state = 0

        self.term = 0
        self.log = [] # list[tuple(term, entry)]
        self.commit_index = 0
        self.last_applied = 0
        self.voted_for = None
        self.node_type = "F"
        self.votes_received = set()
        self.election_timout = self.calculate_election_timeout()

    def calculate_election_timeout(self):
        self.rng.randint(*self.conf["heartbeat_window"])

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
>>>>>>> 23be9ba... Fix typos in node and worldbroker

    def receive(self,sender,message):
        pass

    def timer_trip(self):
        pass

    def loaded_file(self,file_name,data):
        pass

    def saved_file(self,file_name):
        pass
