# Gunicorn Debugging Guide

The debugging instructions below have been tested on PyCharm 2017.1.

### Enable debugging compatibility

In PyCharm, go to:

    Settings > Project Settings > Python Debugger
    
Then enable "Gevent compatible".

### Setup debug configuration

Create a new *Python debug configuration* with these parameters:

- **Script:** path of your gunicorn installation (e.g. "/usr/local/bin/gunicorn3")
- **Script parameters:** "-b {*address:port*} --reload -t 50000 main:app"
- **Environment variables:** "*path/to/your/configuration/file.ini*"
- **Working directory:** "*/path/to/your/frog4-sdn-orchestrator*"

### Start debugging

At this point all you need is to run the orchestrator by using the debug button in PyCharm.