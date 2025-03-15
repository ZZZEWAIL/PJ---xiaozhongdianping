document.getElementById('login-form').addEventListener('submit', async function (event) {
    event.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorMessage = document.getElementById('error-message');

    errorMessage.textContent = '';

    if (!username || !password) {
        errorMessage.textContent = '用户名和密码不能为空';
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            errorMessage.textContent = data.detail || '登录失败';
            return;
        }

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('token_type', data.token_type);

        window.location.href = 'index.html';
    } catch (error) {
        errorMessage.textContent = '网络错误，请稍后重试';
        console.error('Login error:', error);
    }
});