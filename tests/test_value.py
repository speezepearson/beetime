from beetime.ping import Ping
from beetime.value import get_value

def test_get_value():
  assert get_value(Ping(unix_time=0, tags={'$1', '$34'}, comment='')) == 35
