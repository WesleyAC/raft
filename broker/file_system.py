from hypothesis.stateful import GenericStateMachine
from hypothesis.strategies import tuples, sampled_from, just, integers, one_of
from collections import namedtuple


class FileBroker(GenericStateMachine):
    """
    FileBroker manages the interaction with the file system, and emulates slow reads and writes.

    """
    def __init__(self,nodes):
        self.fs_queue = []
        self.nodes = nodes
        self.files = {}

    def steps(self):
        if len(self.fs_queue) > 1:
            return one_of(tuples(just('Resolve')),
                          tuples(just('Delay',integers(min_value=1,
                                                       max_value=len(self.fs_queue)-2))))
        if len(self.fs_queue) == 1:
            return just(tuples(just('Resolve')))
        return just(None)

    def execute_step(self, step):
        if step[0] == 'Resolve':
            self.handle_next_fs()
        elif step[0] == 'Delay':
            Delay = step[1]
            fs_bumped = self.fs_queue.pop()
            self.fs_queue = self.fs_queue[0:-delay] + [fs_bumped] + self.fs_queue[-delay:]


    def handle_next_fs(self):
        """
        handle_next_fs is the glue that binds the deterministic state machine to the actual behavior we want in the file broker.
        It should only ever be called by execute_step (which in turn should only ever be called by hypothesis).
        """
        next_fs = self.fs_queue.pop(0)
        if next_fs:
            if next_fs[0] == 'read':
                op,node_id,file_name = next_fs
                data = self.files[(node_id,file_name)]
                self.nodes.loaded_file(file_name,data)
            elif next_fs[0] == 'write':
                op,node_id,file_name,data = next_fs
                # TODO: CORRUPTION GOES HERE
                self.files[(node_id,file_name)] = data
                self.nodes[node_id].saved_file(file_name)

    # read_file and write_file are the public(used by cluster members) interface

    # nodes must implement loaded_file and saved_file, as they will be called when these async operations are complete.

    def read_file(self,node_id,file_name):
        self.fs_queue.append(('read',node_id,file_name))

    def write_file(self,node_id,file_name,data):
        self.fs_queue.append(('write',node_id,file_name,data))
