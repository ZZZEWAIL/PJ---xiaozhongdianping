document.addEventListener('DOMContentLoaded', async function () {
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');
    const logoutButton = document.getElementById('logout-btn');

    // 检查用户是否已登录
    try {
        const response = await fetch('http://127.0.0.1:8000/auth/protected-endpoint', {
            method: 'GET',
            credentials: 'include', // 确保请求携带 Cookie
        });

        if (response.ok) {
            const data = await response.json();
            console.log('User already logged in:', data);

            // 动态显示用户名
            const usernameElement = document.getElementById('username');
            if (usernameElement) {
                usernameElement.textContent = data.username;
            }

            // 提示用户已登录并跳转到主页
            alert(`您已登录为 ${data.username}，即将跳转到主页。`);
            window.location.href = 'index.html'; // 跳转到主页
            return;
        }
    } catch (error) {
        console.error('Error checking login status:', error);
        // 不做任何操作，用户可以继续登录
    }

    // 登录表单提交逻辑
    if (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('http://127.0.0.1:8000/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                    credentials: 'include', // 确保请求携带 Cookie
                });

                const data = await response.json();

                if (response.ok) {
                    console.log('Login successful', data);

                    // 跳转到主页
                    window.location.href = 'index.html';
                } else {
                    console.error('Login failed', data);
                    alert(data.detail || '用户名或密码错误');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('网络错误，请稍后重试');
            }
        });
    } else {
        console.error('Login form not found');
    }

    // 登出按钮逻辑
    if (logoutButton) {
        logoutButton.addEventListener('click', async function () {
            try {
                const response = await fetch('http://127.0.0.1:8000/auth/logout', {
                    method: 'POST',
                    credentials: 'include', // 确保请求携带 Cookie
                });

                if (response.ok) {
                    alert('您已成功登出');
                    window.location.href = 'login.html'; // 跳转到登录页面
                } else {
                    console.error('Logout failed:', response.status);
                    alert('登出失败，请稍后重试');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('网络错误，请稍后重试');
            }
        });
    } 
});