from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers, one_of

class NetworkBroker(GenericStateMachine):
    """
    Broker to coordinate network traffic

    nodes = A map of node ids to node objects.
    network = An adjacency list of what nodes can talk to each other. If a is
        in network[b] than b -> a communcation is allowed. This is a map of
        id type -> set(id type)
    messages = A queue of messages. messages[0] is the head, where messages are
        sent from. Messages are tuples in the form of (from, to, data).
    """
    def __init__(self, nodes):
        self.nodes = nodes
        self.network = dict([(i, set(nodes.keys())) for i in nodes.keys()])
        self.messages = []

    def send_to(self, sender, to, data):
        self.messages.append((to, sender, data))

    def steps(self):
        #TODO(Wesley) Make more clear
        existing_edges = sum([[(a[0], b) for b in a[1]] for a in self.network.items()], [])
        broken_edges = sum([[(a[0], b) for b in (set(self.nodes.keys()) - a[1]) if a[0] != b] for a in self.network.items()], [])

        deliver_msg = tuple(just("DeliverMsg"))
        drop_msg = tuple(just("DropMsg"))
        duplicate_msg = tuple(just("DuplicateMsg"))
        delay_msg = tuple(just("DelayMsg"), integers(min_value=1, max_value=len(self.messages)))
        destroy_edge = tuple(just("DestroyEdge"), sampled_from(existing_edges))
        heal_edge = tuple(just("HealEdge"), sampled_from(broken_edges))

        actions = []

        if len(existing_edges) > 0:
            actions.append(destroy_edge)

        if len(broken_edges) > 0:
            actions.append(heal_edge)

        if len(self.messages) != 0:
            actions.append(deliver_msg)
            actions.append(drop_msg)
            actions.append(duplicate_msg)
            actions.append(delay_msg)

        return one_of(actions)

    def execute_step(self, step):
        """
        Actions:
        DeliverMsg
            If next message is deliverable, deliver it. Otherwise, drop it.
        DropMsg
            Drop the next message.
        DestroyEdge (from, to)
            Destroys the edge from -> to, causing any packets sent along it to be dropped.
        HealEdge (from, to)
            Heal the edge from -> to, allowing packets to be sent along it.
        DuplicateMsg
            Create a copy of the message at the front of the queue
        DelayMsg n
            Push the message at the front of the queue back by n slots
        """
        action = step[0]
        value = step[1:]
        if action == "DeliverMsg":
            message = self.messages.pop(0)
            self.nodes[message[1]].recv(message[0], message[2])
        if action == "DropMsg":
            self.messages.pop(0)
        if action == "DestroyEdge":
            self.network[step[0]].remove(step[1])
        if action == "HealEdge":
            self.network[step[0]].add(step[1])
        if action == "DuplicateMsg":
            self.messages.insert(0, self.messages[0])
        if action == "DelayMsg":
            self.messages.insert(value, self.messages.pop(0))
