from copy import copy
from node import DownNode

class Event(object):
    """
    The Base Event Class. Includes shared behavior.
    """
    def __init__(self,event_map):
        self.event_map = copy(event_map)
    def __lt__(self,other):
        return self.event_map['start_time'] < other.event_map['start_time']
    def __eq__(self,other):
        # WARNING: this completely breaks object equality.
        return self.event_map['start_time'] == other.event_map['start_time']
    def get_start_time(self):
        return self.event_map['start_time']
    def backout(self): return []
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

# --------------------------Network Management------------------------------------

class NetworkEvent(Event):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker): pass

class DeliveryDrop(NetworkEvent):
    def __init__(self,event_map):
        super().__init__(event_map)
    def backout(self): return [StopDeliveryDrop(self.window_terminus())]

class StopDeliveryDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)

class DeliveryDelay(NetworkEvent):
    def __init__(self,event_map):
        super().__init__(event_map)

    def backout(self):
        return [StopDeliveryDelay(self.window_terminus())]

class StopDeliveryDelay(NetworkEvent):
    def __init__(self,event_map):
        super().__init__(event_map)

class ReceiveDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def backout(self): return [StopDeliveryDrop(self.window_terminus())]
    def handle(self,nodes,network_broker):
        for to_node in self.event_map['affected_nodes']:
            for from_node in nodes:
                network_broker['connections'].discard((from_node,to_node))

class StopReceiveDrop(NetworkEvent):
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
    def backout(self): return [StopTransmitDrop(self.window_terminus())]
    def handle(self,nodes,network_broker):
        pair = self.event_map['affected_node_pair']
        network_broker['connections'].discard(pair)

class StopTransmitDrop(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        pair = self.event_map['affected_node_pair']
        network_broker['connections'].add(pair)

class DeliveryDuplicate(NetworkEvent):
    """
    DeliveryDuplicates Represents all messaages that a node attempts to deliver being duplicated.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def backout(self): return [StopDeliveryDuplicate(self.window_terminus())]
    def handle(self,nodes,network_broker):
        from_node = self.event_map['affected_node']
        for to_node in nodes:
            if from_node != to_node:
                network_broker['duplicates'][(from_node,to_node)] += 1

class StopDeliveryDuplicate(NetworkEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,network_broker):
        from_node = self.event_map['affected_node']
        for to_node in nodes:
            if from_node != to_node:
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
    def backout(self): return [StopPowerDown(self.window_terminus())]
    def handle(self,nodes,power_broker):
        node_id = self.event_map['affected_node']
        if node_id not in power_broker['down_nodes']:
            power_broker['down_nodes'][node_id] =  power_broker['nodes'][node_id]
            power_broker['nodes'][node_id] = DownNode()

class StopPowerDown(PowerEvent):
    """
    StopPowerDown Represents a node coming back up.
    """
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker):
        node_id = self.event_map['affected_node']
        if node_id in power_broker['down_nodes']:
            power_broker['nodes'][node_id] = power_broker['down_nodes'][node_id]
            del power_broker['down_nodes'][node_id]


class HealPower(PowerEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,power_broker):
        for node_id,node in power_broker['down_nodes']:
            power_broker['nodes'][node_id] = node
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
        time_broker['node_time_offsets'][self.event_map['affected_node']] += self.event_map['skew_amount']

class HealTimer(TimerEvent):
    def __init__(self,event_map): super().__init__(event_map)
    def handle(self,nodes,time_broker):
        for node_id in time_broker['node_timers']:
            time_broker['node_timers'][node_id] = 0

