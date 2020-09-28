import pytest

from beetime.ping import Ping, parse_timepie

def test_parse_timepie():
  assert list(parse_timepie([
    '1584884688 sleep  [2020.03.22 06:44:48 Sun]',
    '1584970824  [2020.03.23 06:40:24 Mon]',
    '1584911787 screen/n walking social endorsed  [2020.03.22 14:16:27 Sun]',
  ])) == [
    Ping(unix_time=1584884688, tags=frozenset({'sleep'}), comment='2020.03.22 06:44:48 Sun'),
    Ping(unix_time=1584970824, tags=frozenset(), comment='2020.03.23 06:40:24 Mon'),
    Ping(unix_time=1584911787, tags=frozenset({'screen/n', 'walking', 'social', 'endorsed'}), comment='2020.03.22 14:16:27 Sun'),
  ]

  with pytest.raises(ValueError):
    parse_timepie(['foo'])
