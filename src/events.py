from copy import copy

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
class StopReceiveDrop:
    def __init__(self,event_map): super().__init__(event_map)

class TransmitDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopTransmitDrop(self.window_terminus())
class StopTransmitDrop:
    def __init__(self,event_map): super().__init__(event_map)

class DeliveryDuplicate(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopDeliveryDuplicate(self.window_terminus())
class StopDeliveryDuplicate:
    def __init__(self,event_map): super().__init__(event_map)

class DeliverMessage(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)

class PowerEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker): pass
class PowerDown(PowerEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def reverse(self): return StopPowerDown(self.window_terminus())
class StopPowerDown(PowerEvent):
    def __init__(self,event_map): super().__init__(event_map)


class TimerEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,time_broker): pass
class ClockSkew(TimerEvent):
    def __init__(self,event_map): super().__init__(event_map)









# class PowerBroker(GenericStateMachine):
#     """
#     Starts and stops nodes
#     nodes = A map of node ids to node objects
#     """
#     def __init__(self, nodes):
#         self.up_nodes = nodes
#         self.down_nodes = {}
#     def steps(self):
#         return one_of([tuples(just("Stop"), sample_from(self.up_nodes.keys())),
#                        tuples(just("Start"), sample_from(self.down_nodes.keys()))])
#     def execute_step(self, step):
#         """
#         Actions:
#         Start node_id
#         Stop node_id
#         """
#         action, value = step
#         #TODO(Wesley) Insert DownNode into up_nodes when killing a node
#         if action == "Start":
#             if type(down_nodes[value]) == Node:
#                 self.up_nodes[value] = self.down_nodes.pop(value)
#         elif action == "Stop":
#             if type(up_nodes[value]) == DownNode:
#                 self.down_nodes[value] = self.up_nodes.pop(value)
#                 self.up_nodes[value] = DownNode()



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




