document.addEventListener('DOMContentLoaded', async function () {
    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');
    const errorMessage = document.getElementById('error-message');

    // 验证用户是否已登录
    try {
        const response = await fetch('http://127.0.0.1:8000/auth/protected-endpoint', {
            method: 'GET',
            credentials: 'include',
        });

        if (!response.ok) {
            // 如果未登录或身份验证失败，显示提示
            if (errorMessage) {
                errorMessage.textContent = '请先登录';
            }
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000); // 延迟 2 秒后跳转
            return;
        }

        const data = await response.json();

        // 动态显示用户名和登录时间
        document.getElementById('username').textContent = data.username;
        document.getElementById('login-time').textContent = new Date().toLocaleString();
    } catch (error) {
        console.error('Error:', error);
        if (errorMessage) {
            errorMessage.textContent = '网络错误，请稍后重试';
        }
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return;
    }

    // 切换侧边栏
    document.querySelector('nav').addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return;
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
    });

    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', async function () {
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });

            if (response.ok) {
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