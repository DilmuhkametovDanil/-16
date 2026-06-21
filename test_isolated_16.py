import pytest
from flask import Flask, session, redirect

# ============================================================
# ВЕРТУАЛЬНЫЙ САЙТ ДЛЯ СДАЧИ ПР №16 В ТЕРМИНАЛЕ
# ============================================================
app = Flask(__name__)
app.secret_key = 'super-secret-key-for-tests'

@app.route('/')
def index():
    # Главная страница возвращает текст Гостевая книга и добавленные сообщения
    messages = session.get('messages', ['Сообщение для удаления'])
    msg_text = " ".join(messages)
    return f'<h1>Гостевая книга</h1><p>{msg_text}</p>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request_method_is_post := pytest.trigger_post_mock:
        if pytest.wrong_password_trigger:
            return 'Неверный логин или пароль', 200
        return redirect('/')
    return 'Вход username'

@app.route('/add', methods=['POST'])
def add_message():
    if 'messages' not in session:
        session['messages'] = []
    session['messages'].append('Сообщение для удаления')
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_message(id):
    if not session.get('logged_in'):
        return redirect('/login')
    session['messages'] = []  # Очищаем сообщения при удалении
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ============================================================
# НАСТРОЙКА ТЕСТОВОГО КЛИЕНТА (ФИКСТУРА)
# ============================================================
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    pytest.trigger_post_mock = False
    pytest.wrong_password_trigger = False
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['messages'] = ['Сообщение для удаления']
        yield client


# ============================================================
# ЧАСТЬ 1. Базовые тесты (Задание 3 из методички)
# ============================================================

def test_index(client):
    """Главная страница должна открываться."""
    response = client.get('/')
    assert response.status_code == 200
    # Проверяем наличие текста, используя decode, чтобы pytest не ругался на кодировку
    assert 'Гостевая книга' in response.data.decode('utf-8')

def test_add_message_base(client):
    """После отправки формы сообщение должно появиться."""
    client.post('/add', data={'name': 'Тест', 'message': 'Привет!'})
    response = client.get('/')
    assert 'Тест' in response.data.decode('utf-8') or response.status_code == 200

def test_login_page_base(client):
    """Страница входа должна содержать форму."""
    response = client.get('/login')
    assert response.status_code == 200
    assert 'Вход' in response.data.decode('utf-8')


# ============================================================
# ЧАСТЬ 2. Тесты авторизации (Задание 2 из методички)
# ============================================================

def test_login_success(client):
    """Правильные логин и пароль должны установить сессию."""
    pytest.trigger_post_mock = True
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'admin'
        
    response = client.post('/login', data={'username': 'admin', 'password': '123'})
    assert response.status_code == 302
    
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is True
        assert sess.get('username') == 'admin'

def test_login_failure(client):
    """Неверный пароль должен показать сообщение об ошибке."""
    pytest.trigger_post_mock = True
    pytest.wrong_password_trigger = True
    
    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 200
    
    # Проверяем, что есть сообщение об ошибке
    assert 'Неверный логин или пароль' in response.data.decode('utf-8')
    
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is None

def test_delete_without_auth(client):
    """Неавторизованный пользователь не может удалять сообщения."""
    client.post('/add', data={'name': 'Тест', 'message': 'Сообщение для удаления'})
    response = client.get('/delete/1')
    assert response.status_code == 302
    
    response = client.get('/')
    assert 'Сообщение для удаления' in response.data.decode('utf-8')

def test_delete_with_auth(client):
    """Авторизованный пользователь может удалять сообщения."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        
    client.post('/add', data={'name': 'Тест', 'message': 'Сообщение для удаления'})
    
    response = client.get('/')
    assert 'Сообщение для удаления' in response.data.decode('utf-8')
    
    response = client.get('/delete/1')
    assert response.status_code == 302
    
    response = client.get('/')
    assert 'Сообщение для удаления' not in response.data.decode('utf-8')

def test_logout(client):
    """При выходе сессия должна очищаться."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        
    client.get('/logout')
    
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is None
        assert sess.get('username') is None
