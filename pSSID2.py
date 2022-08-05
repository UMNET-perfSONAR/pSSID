from schedule2 import Schedule
from parse_config import Parse, tests
import argparse
import subprocess as sp
import daemon

parser = argparse.ArgumentParser(description='pSSID')
parser.add_argument('file', action='store',
  help='json file')
parser.add_argument('--debug', action='store_true',
  help='sanity check')
args = parser.parse_args()

# read config file
# call function in parse_config.py
# parse_config.py sub-main will validate that the config file is correct

config_file = open(args.file, "r")
parsed_file = Parse(config_file)
config_file.close() 

schedule = Schedule(parsed_file)
print("daemonizing")
with daemon.DaemonContext():
  schedule.initial_schedule()
  schedule.s.run()