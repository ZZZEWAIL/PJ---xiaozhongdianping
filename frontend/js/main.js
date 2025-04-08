document.addEventListener('DOMContentLoaded', async function () {
    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');
    const errorMessage = document.getElementById('error-message');

    // 验证用户是否已登录
    try {
        const response = await fetch('http://127.0.0.1:8000/auth/protected-endpoint', {
            method: 'GET',
            credentials: 'include', // 确保请求携带 Cookie
        });

        if (!response.ok) {
            // 如果未登录或身份验证失败，跳转到登录页面
            window.location.href = 'login.html';
            return;
        }

        const data = await response.json();

        // 动态显示用户名和登录时间
        document.getElementById('username').textContent = data.username;
        document.getElementById('login-time').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error:', error);
        errorMessage.textContent = '网络错误，请稍后重试';
        window.location.href = 'login.html';
        return;
    }

    // 切换侧边栏
    document.querySelector('nav').addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return; // 防止点击链接时触发
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
    });

    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', async function () {
        try {
            // 调用后端的登出接口，清除 Cookie
            const response = await fetch('http://127.0.0.1:8000/auth/logout', {
                method: 'POST',
                credentials: 'include', // 确保请求携带 Cookie
            });

            if (response.ok) {
                // 跳转到登录页面
                window.location.href = 'login.html';
            } else {
                console.error('Logout failed');
                alert('退出登录失败，请稍后重试');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('网络错误，请稍后重试');
        }
    });
});