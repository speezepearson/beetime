import collections
import dataclasses
import datetime
import json
import logging
import re
import sys
import typing as t

import requests

logger = logging.getLogger(__name__)

UnixTime = int

@dataclasses.dataclass(frozen=True)
class Ping:
  unix_time: UnixTime
  tags: t.FrozenSet[str]
  comment: str

def parse_timepie(lines: t.Iterable[str]) -> t.Iterator[Ping]:
  for line in lines:
    m = re.match(r'^(?P<ts>[0-9]+) (?P<tags>[^\[]*) \[(?P<comment>.*)\]', line)
    if m is None:
      raise ValueError(line)
    yield Ping(
      unix_time=int(m.group('ts')),
      tags=frozenset(word for word in m.group('tags').split(' ') if word),
      comment=m.group('comment'),
    )

assert list(parse_timepie([
  '1584884688 sleep  [2020.03.22 06:44:48 Sun]',
  '1584970824  [2020.03.23 06:40:24 Mon]',
  '1584911787 screen/n walking social endorsed  [2020.03.22 14:16:27 Sun]',
])) == [
  Ping(unix_time=1584884688, tags=frozenset({'sleep'}), comment='2020.03.22 06:44:48 Sun'),
  Ping(unix_time=1584970824, tags=frozenset(), comment='2020.03.23 06:40:24 Mon'),
  Ping(unix_time=1584911787, tags=frozenset({'screen/n', 'walking', 'social', 'endorsed'}), comment='2020.03.22 14:16:27 Sun'),
]
try: _bad = list(parse_timepie(['foo']))
except ValueError: pass
else: assert False, _bad


GoalName = str

class BeeminderClient:
  def __init__(self, user: str, token: str):
    self.user = user
    self.token = token

  def post_pings(self, goal: GoalName, ping_values: t.Mapping[Ping, float]) -> requests.Response:
    payload = [
      {
        'timestamp': ping.unix_time,
        'value': value,
        'comment': f'{ping.unix_time} {" ".join(sorted(ping.tags))} [{ping.comment}]',
        'requestid': str(ping.unix_time),
      }
      for ping, value in ping_values.items()
      if value != 0
    ]
    jpayload = json.dumps(payload)
    logger.info(f'sending request to update {self.user}/{goal} with {len(payload)} datapoints ({len(jpayload)} chars)')
    logger.debug(f'payload: {jpayload}')
    return requests.post(
      url=f'https://www.beeminder.com/api/v1/users/{self.user}/goals/{goal}/datapoints/create_all.json',
      data={
        'auth_token': self.token,
        'datapoints': jpayload,
      }
    )


  def sync(
    self,
    timepie_lines: t.Iterable[str],
    scorers: t.Mapping[GoalName, t.Callable[[Ping], float]],
  ) -> None:
    pings = list(parse_timepie(timepie_lines))
    for goal, score in scorers.items():
      # resp_json = requests.get(f'https://www.beeminder.com/api/v1/users/{beeminder_user}/goals/{goal}/datapoints.json?auth_token={beeminder_token}').json()
      # datapoints_by_time = {
      #   dp['timestamp']: dp
      #   for dp in resp_json
      # }
      resp = self.post_pings(
        goal=goal,
        ping_values={
          ping: score(ping)
          for ping in pings
          if ('OFF' not in ping.tags)
        },
      )
      if resp.status_code != 200:
        logger.warn(f'non-200 status code for {goal}: {resp.status_code}')
        logger.warn(f'details: {resp.text!r}')
      else:
        logger.debug(f'response: {resp.text!r}')

def load_scorers(python_code: str) -> t.Mapping[GoalName, t.Callable[[Ping], float]]:
  loc: t.Mapping
  glob: t.Mapping
  loc = glob = {}
  exec(python_code, glob, loc)
  return loc['SCORERS']

assert load_scorers('SCORERS = {"test-goal": lambda ping: 0.75 if "foo" in ping.tags else 0}')['test-goal'](Ping(unix_time=0, tags=frozenset({'foo'}), comment='')) == 0.75

def demo():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', action='count', default=0)
  args = parser.parse_args()
  logging.basicConfig(level=logging.WARN if args.verbose==0 else logging.INFO if args.verbose==1 else logging.DEBUG)
  client = BeeminderClient(user='speeze', token=open('token.secret').read())
  client.sync(timepie_lines=sys.stdin, scorers={'test-goal': lambda ping: (0.75 if 'sleep' in ping.tags else None)})

if __name__ == "__main__":
  demo()