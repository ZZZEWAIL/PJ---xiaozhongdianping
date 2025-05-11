/**
 * My Orders Page JavaScript
 * 
 * This file handles fetching and displaying the user's orders with pagination.
 */

// API 基础URL
const API_BASE = "http://127.0.0.1:8000/api";

// 分页参数
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;

/**
 * 页面初始化
 */
function initPage() {
    console.log("initPage");
    // 绑定分页按钮事件
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            fetchOrders();
        }
    });

    document.getElementById('next-page').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            fetchOrders();
        }
    });

    // 加载订单数据
    fetchOrders();
}

/**
 * 获取用户订单列表
 */
async function fetchOrders() {
    console.log("fetchOrders");
    try {
        // 显示加载状态
        document.getElementById('orders-loading').style.display = 'block';
        document.getElementById('orders-container').style.display = 'none';
        document.getElementById('no-orders').style.display = 'none';
        document.getElementById('error-container').style.display = 'none';

        const response = await fetch(
            `${API_BASE}/user/orders?page=${currentPage}&page_size=${pageSize}`, {}
        );

        console.log(response);

        if (!response.ok) {
            if (response.status === 401) {
                // 处理授权错误
                document.getElementById('orders-loading').style.display = 'none';
                document.getElementById('login-required').style.display = 'block';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayOrders(data);
    } catch (error) {
        console.error('获取订单列表失败:', error);
        document.getElementById('orders-loading').style.display = 'none';
        document.getElementById('error-container').style.display = 'block';
    }
}

/**
 * 显示订单列表
 * @param {Object} data - 包含订单列表和分页信息的数据对象
 */
function displayOrders(data) {
    // 隐藏加载状态
    document.getElementById('orders-loading').style.display = 'none';

    // 更新分页信息
    currentPage = data.page || 1;
    totalPages = data.total_pages || 1;
    updatePaginationControls();

    // 获取订单列表容器
    const ordersContainer = document.getElementById('orders-container');
    const ordersList = document.getElementById('orders-list');
    const noOrdersContainer = document.getElementById('no-orders');

    // 检查是否有订单
    if (!data.data || data.data.length === 0) {
        ordersContainer.style.display = 'none';
        noOrdersContainer.style.display = 'block';
        return;
    }

    // 显示订单容器
    ordersContainer.style.display = 'block';
    noOrdersContainer.style.display = 'none';

    // 清空订单列表
    ordersList.innerHTML = '';

    // 添加订单行
    data.data.forEach(order => {
        // 格式化日期
        const orderDate = new Date(order.created_at);
        const formattedDate = formatDate(orderDate);

        // 创建行元素
        const tr = document.createElement('tr');
        tr.className = 'order-row';
        tr.setAttribute('data-order-id', order.id);

        tr.innerHTML = `
            <td>${order.package_title}</td>
            <td>${order.shop_name}</td>
            <td>${formattedDate}</td>
            <td>
                <a href="voucher.html?order_id=${order.id}" class="btn btn-sm btn-outline-primary">
                    查看券码
                </a>
            </td>
        `;

        // 添加点击事件，跳转到券码页面
        tr.addEventListener('click', (e) => {
            // 如果点击的是按钮，不需要额外处理（按钮自带跳转）
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }

            // 如果点击表格其他部分，也跳转到券码页面
            window.location.href = `voucher.html?order_id=${order.id}`;
        });

        // 添加到订单列表
        ordersList.appendChild(tr);
    });
}

/**
 * 更新分页控件状态
 */
function updatePaginationControls() {
    // 更新页码信息
    document.getElementById('page-info').textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;

    // 更新按钮状态
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
}

/**
 * 格式化日期为友好显示格式
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date) {
    // 检查是否为有效日期
    if (!(date instanceof Date) || isNaN(date)) {
        return '未知日期';
    }

    // 今天和昨天特殊显示
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date >= today) {
        return `今天 ${formatTime(date)}`;
    } else if (date >= yesterday) {
        return `昨天 ${formatTime(date)}`;
    }

    // 其他日期显示完整日期
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');

    return `${year}-${month}-${day} ${formatTime(date)}`;
}

/**
 * 格式化时间部分
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的时间字符串 (HH:MM)
 */
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// 页面加载时初始化
window.onload = initPage;