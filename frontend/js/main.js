document.addEventListener('DOMContentLoaded', async function () {
    const sidebar = document.querySelector('.vertical-nav');
    const content = document.querySelector('.page-content');
    const errorMessage = document.getElementById('error-message');
    const sortBySelect = document.getElementById('sort-by');
    const shopList = document.getElementById('shop-list');

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

    // 监听排序选项变化
    sortBySelect.addEventListener('change', async function () {
        const sortBy = sortBySelect.value;
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/shops/search?keyword=&sort_by=${sortBy}&sort_order=asc`, {
                method: 'GET',
                credentials: 'include',
            });

            if (response.ok) {
                const shops = await response.json();
                // 清空原有的商家列表
                shopList.innerHTML = '<h3>商家列表</h3>';
                // 渲染新的商家列表
                shops.forEach(shop => {
                    const card = document.createElement('div');
                    card.classList.add('card');
                    card.innerHTML = `
                        <h4><a href="shop_detail.html?id=${shop.id}">${shop.name}</a></h4>
                        <p>类别: ${shop.category}</p>
                        <p>评分: ${shop.rating}</p>
                        <p>人均消费: ${shop.avg_cost}</p>
                    `;
                    shopList.appendChild(card);
                });
            } else {
                console.error('获取商家列表失败');
                alert('获取商家列表失败，请稍后重试');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('网络错误，请稍后重试');
        }
    });
});