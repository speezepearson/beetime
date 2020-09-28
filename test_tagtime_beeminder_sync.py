from beetime.tagtime_beeminder_sync import load_scorers
from beetime.ping import Ping

def test_load_scorers():
  scorers = load_scorers('SCORERS = {"test-goal": lambda ping: 0.75 if "foo" in ping.tags else 0}')
  assert set(scorers.keys()) == {'test-goal'}
  assert scorers['test-goal'](Ping(unix_time=0, tags=frozenset({'foo'}), comment='')) == 0.75
  assert scorers['test-goal'](Ping(unix_time=0, tags=frozenset({'not foo'}), comment='')) == 0
