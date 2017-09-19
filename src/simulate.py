#!/usr/local/bin/python3

from optparse import OptionParser
import sys
import unittest
from world_broker import WorldBroker
from hypothesis import settings
from hypothesis.stateful import find_breaking_runner
from hypothesis.errors import NoSuchExample
from hypothesis.control import BuildContext
from hypothesis.internal.conjecture.data import StopTest

class Simulate(unittest.TestCase):
    "Runs the Simulation"

    CATASTROPHY = 0
    MS_PER_STEP = 700
    MAX_MS_PER_EVENT = 400
    MAX_STEPS = 50
    MAX_ATTEMPTS = 200

    # pylint: disable=no-method-argument
    def test_raft(self):
        "Run the test"
        def init_broker(outside_log=None):
            "Appends a new log to the end of the list"
            if not outside_log:
                latest_log = [{'event_type': 'Simulation Initialization'}]
            else:
                latest_log = outside_log
            return WorldBroker(log=latest_log, catastrophy_level=Simulate.CATASTROPHY,
                               ms_per_step=Simulate.MS_PER_STEP,
                               max_ms_per_event=Simulate.MAX_MS_PER_EVENT)
        
        internal_settings = settings(stateful_step_count=Simulate.MAX_STEPS, max_iterations=Simulate.MAX_ATTEMPTS)
        log = [{'event_type': 'Simulation Initialization'}]
        # print("Attempting with Settings:", Simulate.CATASTROPHY,Simulate.MS_PER_STEP,Simulate.MAX_MS_PER_EVENT)
        try:
            # print("About to find a breaker")
            breaker = find_breaking_runner(init_broker, internal_settings)
            # print("Attempt to find a breaker is done")
        except NoSuchExample:
            # print("Found no such example")
            return
        try:
            # print("Trying this other thing")
            with BuildContext(None, is_final=True):
                # print("Running the breaker we found")
                breaker.run(init_broker(outside_log=log), print_steps=True)
        except StopTest:
            # print("The test Stopped")
            pass
        finally:
            for event in log:
                print(event)
#        raise Flaky(u'Run failed initially but succeeded on a second try')

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", "--catastrophy-level", dest="catastrophy",
                      help="The number of errors to generate per step",
                      action="store", type="int",default=0)
    parser.add_option("-s", "--ms-per-step", dest="ms_per_step",
                      help="The number of ms to emulate per step",
                      action="store", type="int",default=700)
    parser.add_option("-e", "--max-ms-per-event", dest="max_ms_per_event",
                      help="The maximum number of ms that an event can last",
                      action="store", type="int",default=400)
    options, args = parser.parse_args(sys.argv)
    Simulate.CATASTROPHY = options.catastrophy
    Simulate.MS_PER_STEP = options.ms_per_step
    Simulate.MAX_MS_PER_EVENT = options.max_ms_per_event
    suite = unittest.TestSuite()
    suite.addTest(Simulate(methodName='test_raft'))
    unittest.TextTestRunner(verbosity=2).run(suite)

