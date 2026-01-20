from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from routes import routes_bp
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["SECRET_KEY"] = "traffic_police_system_secret_key_2026"

db = SQLAlchemy(app) # инициализируем Алхеми с фласком

app.register_blueprint(routes_bp) # маршруты с файла routes.py

if __name__ == "__main__":
    app.run(debug=True) # запуск приложения и проверка на ошибки
