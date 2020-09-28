import dataclasses
import re
import typing as t

UnixTime = int

@dataclasses.dataclass(frozen=True)
class Ping:
  unix_time: UnixTime
  tags: t.FrozenSet[str]
  comment: str

def parse_timepie_line(line: str) -> Ping:
  m = re.match(r'^(?P<ts>[0-9]+) (?P<tags>[^\[]*) \[(?P<comment>.*)\]', line)
  if m is None:
    raise ValueError(line)
  return Ping(
    unix_time=int(m.group('ts')),
    tags=frozenset(word for word in m.group('tags').split(' ') if word),
    comment=m.group('comment'),
  )

def parse_timepie(lines: t.Iterable[str]) -> t.Sequence[Ping]:
  return [parse_timepie_line(line) for line in lines]
