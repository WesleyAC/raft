class AppendEntries:
    def __init__(self, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit):
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit = leader_commit

class AppendEntriesResponse:
    def __init__(self, term, success):
        self.term = term
        self.success = success

class RequestVote:
    def __init__(self, term, candidate_id, last_log_index, last_log_term):
        self.term = term
        self.candidate_id = candidate_id
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term

class RequestVoteResponse:
    def __init__(self, term, vote_granted):
        self.term = term
        self.vote_granted = vote_granted
