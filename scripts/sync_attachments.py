import argparse
import json
import logging
from pathlib import Path

from beetime.history import History
from beetime.tagtime_beeminder_sync import BeeminderClient, load_scorers
from beetime.fetch_timepies import build_imap, find_timepie_attachments

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='count', default=0)
parser.add_argument('--credentials_file', type=Path, default=Path.home() / '.beetime-credentials.json', help='contains e.g. {"host":"imap.gmail.com", "user":"my.username", "password":"asdfqwerzxcv"}')
parser.add_argument('--history_file', type=Path, default=Path.home() / '.beetime-history.json')
parser.add_argument('--scorers_file', type=Path, default=Path.home() / '.beetime-scorers.py')


def main(args):

  logging.basicConfig(level=logging.WARN if args.verbose==0 else logging.INFO if args.verbose==1 else logging.DEBUG)

  scorers = load_scorers(args.scorers_file.read_text())

  history = History(path=args.history_file)

  _creds = json.load(args.credentials_file.open())
  imap = build_imap(host=_creds['imap']['host'], user=_creds['imap']['user'], password=_creds['imap']['password'])

  client = BeeminderClient(user=_creds['beeminder']['user'], token=_creds['beeminder']['token'])
  timepie_attachments_by_id = find_timepie_attachments(
    imap,
    should_ignore_msg=history.is_msg_processed,
    is_gmail=(_creds['imap']['host']=='imap.gmail.com'),
  )
  for msg_id, pings in timepie_attachments_by_id.items():
    pings = list(pings)
    logger.info(f'found timepie part {msg_id} with {len(pings)} lines')
    client.sync(pings=pings, scorers=scorers)
    history.commit_msg(msg_id)


if __name__ == "__main__":
  main(parser.parse_args())