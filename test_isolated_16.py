from app import app

# ============================================================
# ТЕСТ 1. Успешный вход
# ============================================================

def test_login_success(client):
    """Правильные логин и пароль должны установить сессию."""
    response = client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    
    # Должен быть редирект на главную (код 302)
    assert response.status_code == 302
    
    # Проверяем, что сессия установлена
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is True
        assert sess.get('username') == 'admin'


# ============================================================
# ТЕСТ 2. Неуспешный вход (неверный пароль)
# ============================================================

def test_login_failure(client):
    """Неверный пароль должен показать сообщение об ошибке."""
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'wrong'
    })
    
    # Страница с ошибкой (код 200, а не редирект 302)
    assert response.status_code == 200
    
    # Проверяем, что есть сообщение об ошибке
    assert b'Неверный логин или пароль' in response.data
    
    # Проверяем, что сессия НЕ установлена
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is None


# ============================================================
# ТЕСТ 3. Защита удаления (без авторизации)
# ============================================================

def test_delete_without_auth(client):
    """Неавторизованный пользователь не может удалять сообщения."""
    # Добавляем сообщение
    client.post('/add', data={
        'name': 'Тест',
        'message': 'Сообщение для удаления'
    })
    
    # Пробуем удалить без авторизации
    response = client.get('/delete/1')
    
    # Должен быть редирект на страницу входа
    assert response.status_code == 302
    
    # Проверяем, что сообщение осталось
    response = client.get('/')
    assert b'Сообщение для удаления' in response.data


# ============================================================
# ТЕСТ 4. Удаление с авторизацией
# ============================================================

def test_delete_with_auth(client):
    """Авторизованный пользователь может удалять сообщения."""
    # Сначала входим
    client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    
    # Добавляем сообщение
    client.post('/add', data={
        'name': 'Тест',
        'message': 'Сообщение для удаления'
    })
    
    # Проверяем, что сообщение появилось
    response = client.get('/')
    assert b'Сообщение для удаления' in response.data
    
    # Удаляем
    response = client.get('/delete/1')
    assert response.status_code == 302
    
    # Проверяем, что сообщение исчезло
    response = client.get('/')
    assert b'Сообщение для удаления' not in response.data


# ============================================================
# ТЕСТ 5. Выход из системы
# ============================================================

def test_logout(client):
    """При выходе сессия должна очищаться."""
    # Сначала входим
    client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    
    # Проверяем, что вошли
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is True
    
    # Выходим
    client.get('/logout')
    
    # Проверяем, что вышли
    with client.session_transaction() as sess:
        assert sess.get('logged_in') is None
        assert sess.get('username') is None
