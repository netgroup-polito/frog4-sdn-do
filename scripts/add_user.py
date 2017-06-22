import os
import hashlib
import argparse

from do_core.sql.user import User

os.environ.setdefault("FROG4_SDN_DO_CONF", "config/default-config.ini")


def add_user(username, password, tenant_id=0, mail=None):

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    User().addUser(username, password_hash, tenant_id, mail)

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "user",
    help='Name of the user to add'
)
parser.add_argument(
    "password",
    help='Password of the user'
)
parser.add_argument(
    '-t',
    '--tenant',
    nargs='?',
    default=1,
    help='User tenant'
)
parser.add_argument(
    '-m',
    '--mail',
    nargs='?',
    default=None,
    help='User e-mail'
)
args = parser.parse_args()

add_user(args.user, args.password, tenant_id=args.tenant, mail=args.mail)
