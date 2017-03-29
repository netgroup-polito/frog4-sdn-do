import os
import argparse

from subprocess import call
from do_core.config import Configuration

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
      '-d',
      "--conf_file",
      nargs='?',
      help='Configuration file'
)

args = parser.parse_args()


# set configuration file
if args.conf_file:
    os.environ.setdefault("FROG4_SDN_DO_CONF", args.conf_file)

conf = Configuration()
ip = Configuration().ORCHESTRATOR_IP
port = conf.ORCHESTRATOR_PORT
address = str(ip) + ":" + str(port)

call("gunicorn3 -b " + address + " -w 1 -t 500 main:app", shell=True)
