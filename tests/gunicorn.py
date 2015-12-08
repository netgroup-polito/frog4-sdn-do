from subprocess import call
call("gunicorn -b 0.0.0.0:9000 -t 500 testgu1:app", shell=True)