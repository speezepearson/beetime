import re

from .ping import Ping

def get_value(ping: Ping) -> int:
  # from random import random; return random()*1000
  return sum(int(t[1:]) for t in ping.tags if re.match('^[$][0-9]+$', t))
