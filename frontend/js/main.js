document.addEventListener('DOMContentLoaded', async function () {
    // 退出登录
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function () {
            try {
                console.log('Logout button clicked'); // 添加调试日志
                const response = await fetch('http://127.0.0.1:8000/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    console.log('Logout successful');
                    window.location.href = 'login.html';
                } else {
                    const errorData = await response.json();
                    console.error('Logout failed:', errorData);
                    alert(`退出登录失败: ${errorData.detail || '未知错误'}`);
                }
            } catch (error) {
                console.error('Network error:', error);
                alert('网络错误，请检查控制台');
            }
        });
    } else {
        console.warn('Logout button not found');
    }

    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');
    const errorMessage = document.getElementById('error-message');
    const currentPage = window.location.pathname;

    // 验证用户是否已登录
    if (currentPage.includes('index.html')) {

        try {
            const response = await fetch('http://127.0.0.1:8000/auth/status', {
                method: 'GET',
                credentials: 'include',
            });

            if (!response.ok) {
                console.log('User not authenticated, redirecting to login page.');
                window.location.href = 'login.html'; // 跳转到登录页面
                return;
            }

            const data = await response.json();
            console.log('User authenticated:', data);

            // 动态显示用户名和登陆时间
            document.getElementById('username').textContent = data.username;
            document.getElementById('login-time').textContent = new Date().toLocaleString();

        } catch (error) {
            console.error('Error checking authentication:', error);
            window.location.href = 'login.html'; // 跳转到登录页面
        }
    }

    // 切换侧边栏
    document.querySelector('nav').addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return;
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
    });

    
});