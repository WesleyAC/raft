"""
Classes for each type of message sent between nodes.
"""

# pylint: disable=too-few-public-methods
class AppendEntries:
    """
    Appends an entry to the distributed log
    """
    # pylint: disable=too-many-arguments
    def __init__(self, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit):
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit = leader_commit

    def to_str(self):
        "Returns a string representation of the message"
        return "AppendEntry: {}".format(self.term)

# pylint: disable=too-few-public-methods
class AppendEntriesResponse:
    "The reponse to a request to append"
    def __init__(self, term, success):
        self.term = term
        self.success = success

# pylint: disable=too-few-public-methods
class RequestVote:
    "Request a vote from another node"
    def __init__(self, term, candidate_id, last_log_index, last_log_term):
        self.term = term
        self.candidate_id = candidate_id
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term

# pylint: disable=too-few-public-methods
class RequestVoteResponse:
    "Response to a requested Vote"
    def __init__(self, term, vote_granted):
        self.term = term
        self.vote_granted = vote_granted
