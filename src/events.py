from copy import copy
from node import DownNode

class Event:
    """
    The Base Event Class. Includes shared behavior.
    """
    def __init__(self,event_map):
        self.event_map = copy(event_map)
    def reverse(self): return []
    def window_terminus(self):
        """
        Returns a new event_map with the start at the end of this one, and no event length.
        Used for the reversing event at the end of a window.
        """
        ret = copy(self.event_map)
        event_end = ret['event_length']+ret['start_time']
        del ret['event_length']
        ret['start_time'] = event_end
        return ret
    def prioritize(self):
        return (self.event_map['start_time'],self)

class NetworkEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker): pass

class DeliveryDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopDeliveryDrop(self.window_terminus())
class StopDeliveryDelay:
    def __init__(self,event_map): super().__init__(event_map)

class DeliveryDelay(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopDeliveryDelay(self.window_terminus())
class StopDeliveryDelay:
    def __init__(self,event_map): super().__init__(event_map)


class ReceiveDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopDeliveryDrop(self.window_terminus())
    def handle(self,nodes,network_broker):
        for to_id in self.event_map['affected_nodes']:
            for from_node in nodes:
                network_broker['connections'].discard((from_node,to_node))
class StopReceiveDrop:
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        for to_id in self.event_map['affected_nodes']:
            for from_node in nodes:
                network_broker['connections'].add((from_node,to_node))


class TransmitDrop(NetworkEvent):
    """
    TransmitDrop represents all packets sent between two nodes being dropped.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopTransmitDrop(self.window_terminus())
    def handle(self,nodes,network_broker):
        pair = self.event_map['affected_node_pair']
        network_broker['connections'].discard(pair)

class StopTransmitDrop:
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        pair = self.event_map['affected_node_pair']
        network_broker['connections'].add(pair)


class DeliveryDuplicate(NetworkEvent):
    """
    DeliveryDuplicates Represents all messaages that a node attempts to deliver being duplicated.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopDeliveryDuplicate(self.window_terminus())
    def handle(self,nodes,network_broker):
        from_node = self.event_map['affected_node']
        for to_node in nodes:
            network_broker['duplicates'][(from_node,to_node)] += 1

class StopDeliveryDuplicate:
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        from_node = self.event_map['affected_node']
        for to_node in nodes:
            network_broker['duplicates'][(from_node,to_node)] = max(0,network_broker['duplicates'][(from_node,to_node)] -1)

class DeliverMessage(NetworkEvent):
    """
    DeliverMessage represents the attempted delivery of a message.
    This checks if there is a network disruption that prevents the message from being delivered,
    and the case that power is down on the node is taken care of due to DownNodes in the nodes arg.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        from_node = self.event_map['sender']
        to_node = self.event_map['affected_node']
        if (from_node,to_node) in network_broker['connections']:
            nodes[to_node].receive(from_node,self.event_map['data'])


class HealNetwork(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        network_broker['connections'] = set([(f,t) for f in self.node_ids for t in self.node_ids if t != f])
        network_broker['delays'] = {(f,t):0 for f in self.node_ids for t in self.node_ids if t != f}
        network_broker['duplicates'] = {(f,t):0 for f in self.node_ids for t in self.node_ids if t != f}


# --------------------------Power Management------------------------------------

class PowerEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker): pass

class PowerDown(PowerEvent):
    """
    PowerDown Represents a node shutting down.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopPowerDown(self.window_terminus())
    def handle(self,nodes,power_broker):
        node_id = self.event_map['affected_node']
        if node_id not in power_broker['down_nodes']:
            power_broker['down_nodes'][node_id] =  power_broker['up_nodes'][node_id]
            power_broker['up_nodes'][node_id] = DownNode()

class StopPowerDown(PowerEvent):
    """
    StopPowerDown Represents a node coming back up.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker):
        node_id = self.event_map['affected_node']
        if node_id in power_broker['down_nodes']:
            power_broker['up_nodes'][node_id] = power_broker['down_nodes'][node_id]
            del power_broker['down_nodes'][node_id]


class HealPower(PowerEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker):
        for node_id,node in power_broker['down_nodes']:
            power_broker['up_nodes'][node_id] = node
            del power_broker['down_nodes'][node_id]

#------------------------ Time Management---------------------------------------

class TimerEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,time_broker): pass

class ClockSkew(TimerEvent):
    """
    ClockSkew Represents a one time skew of a clock on an individual node.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,time_broker):
        time_broker['node_time_offsets'][self.event_map['affected_node']] += self.event_map['delay']

class HealTimer(TimerEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,time_broker):
        for node_id in time_broker['node_timers']:
            time_broker['node_timers'][node_id] = 0


# class NetworkBroker(GenericStateMachine):
#     """
#     Broker to coordinate network traffic
#     nodes = A map of node ids to node objects.
#     network = An adjacency list of what nodes can talk to each other. If a is
#         in network[b] than b -> a communcation is allowed. This is a map of
#         id type -> set(id type)
#     messages = A queue of messages. messages[0] is the head, where messages are
#         sent from. Messages are tuples in the form of (from, to, data).
#     """
#     def __init__(self, nodes):
#         self.nodes = nodes
#         self.network = dict([(i, set(nodes.keys())) for i in nodes.keys()])
#         self.messages = []
#     def send_to(self, sender, to, data):
#         self.messages.append((to, sender, data))
#     def steps(self):
#         #TODO(Wesley) Make more clear
#         existing_edges = sum([[(a[0], b) for b in a[1]] for a in self.network.items()], [])
#         broken_edges = sum([[(a[0], b) for b in (set(self.nodes.keys()) - a[1]) if a[0] != b] for a in self.network.items()], [])
#         deliver_msg = tuple(just("DeliverMsg"))
#         drop_msg = tuple(just("DropMsg"))
#         duplicate_msg = tuple(just("DuplicateMsg"))
#         delay_msg = tuple(just("DelayMsg"), integers(min_value=1, max_value=len(self.messages)))
#         destroy_edge = tuple(just("DestroyEdge"), sampled_from(existing_edges))
#         heal_edge = tuple(just("HealEdge"), sampled_from(broken_edges))
#         actions = []
#         if len(existing_edges) > 0:
#             actions.append(destroy_edge)
#         if len(broken_edges) > 0:
#             actions.append(heal_edge)
#         if len(self.messages) != 0:
#             actions.append(deliver_msg)
#             actions.append(drop_msg)
#             actions.append(duplicate_msg)
#             actions.append(delay_msg)
#         return one_of(actions)
#     def execute_step(self, step):
#         """
#         Actions:
#         DeliverMsg
#             If next message is deliverable, deliver it. Otherwise, drop it.
#         DropMsg
#             Drop the next message.
#         DestroyEdge (from, to)
#             Destroys the edge from -> to, causing any packets sent along it to be dropped.
#         HealEdge (from, to)
#             Heal the edge from -> to, allowing packets to be sent along it.
#         DuplicateMsg
#             Create a copy of the message at the front of the queue
#         DelayMsg n
#             Push the message at the front of the queue back by n slots
#         """
#         action = step[0]
#         value = step[1:]
#         if action == "DeliverMsg":
#             message = self.messages.pop(0)
#             self.nodes[message[1]].recv(message[0], message[2])
#         if action == "DropMsg":
#             self.messages.pop(0)
#         if action == "DestroyEdge":
#             self.network[step[0]].remove(step[1])
#         if action == "HealEdge":
#             self.network[step[0]].add(step[1])
#         if action == "DuplicateMsg":
#             self.messages.insert(0, self.messages[0])
#         if action == "DelayMsg":
#             self.messages.insert(value, self.messages.pop(0))




