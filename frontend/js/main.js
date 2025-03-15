document.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('access_token');
    const username = 'Ada'; // 需从 Token 中解析
    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    document.getElementById('username').textContent = username;
    document.getElementById('login-time').textContent = new Date().toLocaleString();

    // 切换侧边栏
    document.querySelector('nav').addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return; // 防止点击链接时触发
        sidebar.classList.toggle('active');
        content.classList.toggle('active');
    });

    document.getElementById('logout-btn').addEventListener('click', function () {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        window.location.href = 'login.html';
    });
});