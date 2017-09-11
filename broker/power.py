from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, one_of

class PowerBroker(GenericStateMachine):
    """
    Starts and stops nodes

    nodes = A map of node ids to node objects
    """

    def __init__(self, nodes):
        self.up_nodes = nodes
        self.down_nodes = {}

    def steps(self):
        return one_of([tuples(just("Stop"), sample_from(self.up_nodes.keys())),
                       tuples(just("Start"), sample_from(self.down_nodes.keys()))])

    def execute_step(self, step):
        """
        Actions:

        Start node_id
        Stop node_id
        """
        action, value = step

        #TODO(Wesley) Insert DownNode into up_nodes when killing a node
        if action == "Start":
            self.up_nodes[value] = self.down_nodes.pop(value)
        elif action == "Stop":
            self.down_nodes[value] = self.up_nodes.pop(value)
