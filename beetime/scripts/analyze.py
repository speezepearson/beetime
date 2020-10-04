import argparse
import collections
import json
from pathlib import Path

import matplotlib.pyplot as plt

from beetime.value import get_value
from beetime.ping import parse_timepie

parser = argparse.ArgumentParser()
parser.add_argument('timepie_log', type=Path)

def mean(xs):
  xs = list(xs)
  return sum(xs) / len(xs)

def main(args):
  timepie_log: Path = args.timepie_log
  del args

  pings = list(parse_timepie(timepie_log.open()))
  print('Mean value per ping:', mean(get_value(ping) for ping in pings))

  all_tags = set().union(*[ping.tags for ping in pings])
  print(f'{"TAG":^20s}    {"$/hr":^7s}    {"n":^5s}')
  for tag in all_tags:
    relevant_pings = [ping for ping in pings if tag in ping.tags]
    mean_value = mean(get_value(ping) for ping in relevant_pings)
    print(f'{tag:^20s}    {int(mean_value): 7.2f}    {len(relevant_pings): 5d}')
    plt.annotate(s=tag, xy=(mean_value, len(relevant_pings)))
    plt.scatter([mean_value], [len(relevant_pings)])

  plt.yscale('log')
  plt.show()

if __name__ == "__main__":
  main(parser.parse_args())
