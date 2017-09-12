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

    def receive(self,sender,message):
        pass

    def timer_trip(self):
        pass

    def loaded_file(self,file_name,data):
        pass

    def saved_file(self,file_name):
        pass
