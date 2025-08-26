import sys

path = "/home/Dm1tryLalov/my-first-blog"
if path not in sys.path:
    sys.path.append(path)

from bot_app import app as application
