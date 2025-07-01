import datetime
import subprocess

def get_version():
    now = datetime.datetime.now()
    return f"{now.year}.{now.month}.{now.day}.{now.hour}{now.minute:02d}"