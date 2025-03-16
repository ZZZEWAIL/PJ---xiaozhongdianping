document.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username'); // 从 localStorage 获取用户名
    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');

    // 未登录时跳转到登录页面
    if (!token || !username) {
        window.location.href = 'login.html';
        return;
    }

    // 动态显示用户名和登录时间
    document.getElementById('username').textContent = username;
    document.getElementById('login-time').textContent = new Date().toLocaleString();

    // 切换侧边栏
    document.querySelector('nav').addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return; // 防止点击链接时触发
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
    });

    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', function () {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('username'); // 清除用户名
        window.location.href = 'login.html';
    });
});