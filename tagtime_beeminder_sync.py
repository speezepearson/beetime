import collections
import dataclasses
import datetime
import json
import logging
import sys
import typing as t

import requests

from .ping import Ping

logger = logging.getLogger(__name__)

GoalName = str

class BeeminderClient:
  def __init__(self, user: str, token: str):
    self.user = user
    self.token = token

  def post_pings(self, goal: GoalName, ping_values: t.Mapping[Ping, float]) -> requests.Response:
    """Upload a bunch of pings and values to a particular Beeminder goal."""
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
    pings: t.Iterable[Ping],
    scorers: t.Mapping[GoalName, t.Callable[[Ping], float]],
  ) -> None:
    """Compute the values for all pings for all goals, and upload the data, overwriting any previous data for the given pings."""
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
  """Parse a `{goal: (ping -> value)}` mapping from Python source code.

  The given `python_code` can be arbitrary Python code, as long as it defines a variable `SCORERS` of the right type.
  """
  loc: t.Mapping[str, t.Any]
  glob: t.Mapping[str, t.Any]
  loc = glob = {}
  exec(python_code, glob, loc)
  return loc['SCORERS']
