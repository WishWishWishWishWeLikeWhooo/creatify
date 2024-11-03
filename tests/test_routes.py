import unittest
from app import create_app, db
from app.models import User
from flask import url_for


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        response = self.client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword'
        }, follow_redirects=True)
        self.assertIn(b'Регистрация прошла успешно!', response.data)

    def test_login_logout(self):
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Вы вошли в систему!', response.data)

        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Добро пожаловать', response.data)

    def test_generate_text(self):
        # Вход
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password'
        }, follow_redirects=True)

        # Генерация текста
        response = self.client.post('/generate-text', data={
            'keywords': 'технологии, искусственный интеллект',
            'tone': 'formal',
            'length': 'medium'
        }, follow_redirects=True)
        self.assertIn(b'Сгенерированный Текст:', response.data)


if __name__ == '__main__':
    unittest.main()
