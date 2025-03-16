document.getElementById('register-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const captcha = document.getElementById('captcha').value;

    const response = await fetch('http://127.0.0.1:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, captcha })
    });

    const data = await response.json();

    if (response.ok) {
        console.log('Registration successful', data);
        alert('Registration successful!');
        window.location.href = '/login'; // 注册成功后跳转到登录页面
    } else {
        console.error('Registration failed', data);
        alert(data.detail || 'Registration failed');
    }
});