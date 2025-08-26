import sys
import os

# Добавляем путь к вашему приложению
path = "/home/Dm1tryLalov/my-first-blog"
if path not in sys.path:
    sys.path.append(path)

# Устанавливаем переменную окружения для Flask
os.environ["FLASK_APP"] = "bot_app"

from bot_app import app as application
