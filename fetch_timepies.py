import email
import email.message
import imaplib
import logging
from pathlib import Path
import typing as t
import json
import re

logger = logging.getLogger(__name__)


class History:
  def __init__(self, path: Path) -> None:
    self.path = path
    j = json.load(path.open()) if path.exists() else {}
    self._processed_msg_ids = set(j.get('processed_msg_ids', []))

  def is_msg_processed(self, msg_id: str) -> bool:
    return msg_id in self._processed_msg_ids

  def commit_msg(self, msg_id: str) -> None:
    self._processed_msg_ids.add(msg_id)
    self._commit()

  def _commit(self) -> None:
    json.dump({'processed_msg_ids': list(sorted(self._processed_msg_ids))}, self.path.open('w'))


def build_imap(host: str, user: str, password: str) -> imaplib.IMAP4_SSL:
  imap = imaplib.IMAP4_SSL(host)
  status, details = imap.login(user, password)
  if status != 'OK':
    raise RuntimeError(f'login failed: {details}')
  logger.debug('logged in')
  return imap


def find_timepie_part(msg: email.message.Message) -> str:
  for part in msg.walk():
    payload = part.get_payload(decode=True)
    if payload is not None:
      if re.match(rb'^[0-9]{7,} [^\[]*\[.*\]\n', payload):
        return payload.decode('utf-8')
  raise ValueError('given message has no timepie.log part')

def find_timepie_attachments(
  imap: imaplib.IMAP4_SSL,
  should_ignore_msg: t.Callable[[str], bool],
  is_gmail: bool = False,
) -> t.Mapping[str, str]:

  status: t.Any
  details: t.Any

  status, details = imap.select('INBOX')
  if status != 'OK':
    raise RuntimeError(f'select failed: {details}')

  status, details = imap.search(None, 'X-GM-RAW "has:attachment subject:timepie.log"' if is_gmail else 'HEADER Subject "timepie.log"')
  if status != 'OK':
    raise RuntimeError(f'bad status on search: {status}')
  msg_ids = set(details[0].decode('utf-8').split(' '))
  logger.debug(f'pre-filter msg_ids = {msg_ids}')

  msg_ids = {m for m in msg_ids if not should_ignore_msg(m)}
  logger.debug(f'post-filter msg_ids = {msg_ids}')

  result = {}
  for msg_id in sorted(msg_ids):
    logger.info(f'fetching msg {msg_ids}')

    msg_info: t.Any
    status, msg_info = imap.fetch(msg_id, '(RFC822)')
    if status != 'OK':
      raise RuntimeError(f'bad status on fetch: {status}')
    msg = email.message_from_bytes(msg_info[0][1])
    try:
      result[msg_id] = find_timepie_part(msg)
    except ValueError:
      logger.info(f'msg {msg_id} has no timepie part')
      continue

  return result
