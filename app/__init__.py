# app/__init__.py
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf import CSRFProtect
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Настройки приложения
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)

    # Настройка представления для входа в систему
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Регистрация Blueprint'ов
    from .routes import main
    app.register_blueprint(main)

    # Инициализация CSRF защиты после регистрации Blueprint'ов
    csrf.init_app(app)

    # Отключение CSRF защиты для API маршрутов (если есть)
    @app.before_request
    def csrf_exempt_api():
        if request.blueprint == 'api':
            csrf.exempt(request.endpoint)

    return app
