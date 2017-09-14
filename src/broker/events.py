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
