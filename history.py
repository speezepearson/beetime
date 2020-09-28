import json
from pathlib import Path

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

