// document.getElementById('login-form').addEventListener('submit', async function(event) {
//     event.preventDefault();

//     const username = document.getElementById('username').value;
//     const password = document.getElementById('password').value;

//     const response = await fetch('http://127.0.0.1:8000/auth/login', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ username, password })
//     });

//     const data = await response.json();

//     if (response.ok) {
//         console.log('Login successful', data);
//         localStorage.setItem('access_token', data.access_token);
//         localStorage.setItem('token_type', data.token_type);
//         window.location.href = 'index.html';
//     } else {
//         console.error('Login failed', data);
//         alert('Invalid username or password');
//     }
// });

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    if (!form) {
        console.error('Login form not found');
        return;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('http://127.0.0.1:8000/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                console.log('Login successful', data);

                // 存储令牌
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('token_type', data.token_type);

                // 解析 JWT 令牌中的用户名
                const payload = JSON.parse(atob(data.access_token.split('.')[1]));
                const loggedInUsername = payload.username;

                // 存储用户名
                localStorage.setItem('username', loggedInUsername);

                // 跳转到首页
                window.location.href = 'index.html';
            } else {
                console.error('Login failed', data);
                errorMessage.textContent = data.detail || '用户名或密码错误';
            }
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = '网络错误，请稍后重试';
        }
    });
});