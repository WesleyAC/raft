How to install requirements:

~~~
pip install -r requirements
~~~

How to run tests:

~~~
pytest src/world_broker.py
~~~

How tests work:

* calls `__init__`, which initializes the cluster.
* calls `step`, which generates a set of potential events (like node failure or clock skew), which are fed `execute_step` function.
* `execute_step` puts those events into a queue and then generates the anti-event (e.g., if the node goes down, a corresponding node up event is created).

Note:
If you want to see print statements, pass `-s` to pytest.