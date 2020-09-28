"""Example `~/.beetime-scorers.py`, specifying how each goal should count each ping.
"""

SCORERS = {
  'test-goal': lambda ping: (0.75 if (1601263350 <= ping.unix_time) and ('sleep' in ping.tags) else 0),
}
