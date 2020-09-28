import json
from pathlib import Path
import typing as t

_PROCESSED_MSG_IDS_KEY = 'processed_msg_ids'

class History:
  def __init__(self, path: Path) -> None:
    self.path = path
    j = json.load(path.open()) if path.exists() else {}
    self._processed_msg_ids = set(j.get(_PROCESSED_MSG_IDS_KEY, []))

  def is_msg_processed(self, msg_id: str) -> bool:
    return msg_id in self._processed_msg_ids

  def commit_msg(self, msg_id: str) -> None:
    self._processed_msg_ids.add(msg_id)
    self._commit()

  def to_json(self) -> str:
    return json.dumps({_PROCESSED_MSG_IDS_KEY: list(sorted(self._processed_msg_ids))})

  def _commit(self) -> None:
    self.path.write_text(self.to_json())
