# Necessary steps to implement RAFT
[ ] Update TimerBroker to recognize proper timer delays
[ ] Verify operation of timer firing
[ ] Add happy path operation to MetaBroker
[ ] Implement Leader Election
[ ] Verify Leader Election properties
1. Manual tests with some cases that work
2. Only one leader in a given term
3. When a majority of nodes are up, there should eventually be a leader
[ ] Log Replication
[ ] Verify Log Replication
1. Once a an entry is committed, it's never deleted
2. Logs are identical across nodes once committed
[ ] State machine counter
[ ] Configuration changes
[ ] Verify Config changes
1. Manual test cases that should work
2. Generative testing that should work
