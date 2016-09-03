from subprocess import call
from do_core.config import Configuration

conf = Configuration()
ip = conf.ORCHESTRATOR_IP
port = conf.ORCHESTRATOR_PORT
address = str(ip) + ":" + str(port)

call("gunicorn3 -b " + address + " -w 1 -t 500 main:app", shell=True)
