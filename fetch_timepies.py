"""Tools for fetching TagTime data from email.
"""

import email
import email.message
import imaplib
import logging
from pathlib import Path
import typing as t
import json
import re

from .ping import Ping, parse_timepie

MsgId = str

logger = logging.getLogger(__name__)


def build_imap(host: str, user: str, password: str) -> imaplib.IMAP4_SSL:
  """Utility to create an IMAP instance and log it in."""
  imap = imaplib.IMAP4_SSL(host)
  status, details = imap.login(user, password)
  if status != 'OK':
    raise RuntimeError(f'login failed: {details}')
  logger.debug('logged in')
  return imap


def _find_timepie_part(msg: email.message.Message) -> t.Sequence[Ping]:
  """Try to find which part of a potentially nested multipart message contains TagTime data."""
  for part in msg.walk():
    payload = part.get_payload(decode=True)
    if payload:
      lines = payload.decode('utf-8').splitlines()
      if lines and all(re.match(r'^[0-9]{7,} [^\[]*\[.*\]$', line) for line in lines):
        return parse_timepie(lines)
  raise ValueError('given message has no timepie.log part')

def find_timepie_attachments(
  imap: imaplib.IMAP4_SSL,
  should_ignore_msg: t.Callable[[MsgId], bool],
  is_gmail: bool = False,
) -> t.Mapping[MsgId, t.Sequence[Ping]]:

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
      result[msg_id] = _find_timepie_part(msg)
    except ValueError:
      logger.info(f'msg {msg_id} has no timepie part')
      continue

  return result
