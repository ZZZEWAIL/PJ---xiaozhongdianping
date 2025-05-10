/**
 * Package Detail Page JavaScript
 * 
 * This file handles fetching and displaying package details as well as
 * the purchase functionality for a specific package.
 */

// 从 URL 获取 package_id
const urlParams = new URLSearchParams(window.location.search);
const packageId = urlParams.get('package_id');
const API_BASE = "http://127.0.0.1:8000/api";

// 存储当前包的数据
let currentPackageData = null;

/**
 * 初始化页面
 */
function initPage() {
    // 检查是否有 package_id
    if (!packageId) {
        showError('未找到套餐 ID');
        return;
    }

    // 获取套餐详情
    fetchPackageDetail();

    // 设置购买按钮事件
    document.getElementById('buy-button').addEventListener('click', handlePurchase);
}

/**
 * 获取套餐详情
 */
async function fetchPackageDetail() {
    try {
        const response = await fetch(`${API_BASE}/packages/${packageId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        currentPackageData = data;

        // 显示套餐信息
        displayPackageDetail(data);

        // 隐藏加载指示器
        document.getElementById('package-loading').style.display = 'none';

        // 显示套餐容器
        document.getElementById('package-container').style.display = 'block';

        // 更新返回商家链接
        if (data.shop_id) {
            document.getElementById('back-to-shop').href = `shops_detail.html?shop_id=${data.shop_id}`;
        }
    } catch (error) {
        console.error('获取套餐详情失败:', error);
        showError('无法加载套餐信息，请稍后重试');
    }
}

/**
 * 显示套餐详情
 * @param {Object} packageData - 套餐数据
 */
function displayPackageDetail(packageData) {
    // 设置标题
    document.getElementById('package-title').textContent = packageData.title;
    document.title = `${packageData.title} - 小众点评`;

    // 设置价格
    const priceFormatted = `¥${packageData.price.toFixed(2)}`;
    document.getElementById('package-price').textContent = priceFormatted;
    document.getElementById('card-price').textContent = priceFormatted;

    // 设置销量
    document.getElementById('package-sales').textContent = `已售 ${packageData.sales} 份`;

    // 设置描述
    document.getElementById('package-description').textContent = packageData.description || '暂无描述';

    // 设置店铺信息
    document.getElementById('package-shop').textContent = packageData.shop_name || '暂无信息';

    // 设置套餐内容
    displayPackageContents(packageData.contents);
}

/**
 * 解析并显示套餐内容
 * @param {string} contentsString - 套餐内容字符串
 */
function displayPackageContents(contentsString) {
    const contentsContainer = document.getElementById('package-contents');
    contentsContainer.innerHTML = '';

    // 如果没有内容，显示提示信息
    if (!contentsString || contentsString.trim() === '') {
        contentsContainer.innerHTML = '<li class="list-group-item">暂无套餐内容信息</li>';
        return;
    }

    // 尝试将内容拆分为项目列表
    // 假设内容是用换行符或分号分隔的
    let contentItems = [];
    if (contentsString.includes('\n')) {
        contentItems = contentsString.split('\n');
    } else if (contentsString.includes(';')) {
        contentItems = contentsString.split(';');
    } else {
        // 如果没有明确的分隔符，就将整个字符串作为一个项目
        contentItems = [contentsString];
    }

    // 添加每个内容项
    contentItems.forEach(item => {
        if (item.trim() !== '') {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            listItem.textContent = item.trim();
            contentsContainer.appendChild(listItem);
        }
    });
}

/**
 * 处理购买按钮点击事件
 */
function handlePurchase() {
    if (!currentPackageData) {
        showError('套餐数据加载失败，无法购买');
        return;
    }

    // 跳转到确认订单页面
    window.location.href = `order_confirm.html?package_id=${packageId}`;
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showError(message) {
    document.getElementById('package-loading').style.display = 'none';

    const errorContainer = document.getElementById('error-container');
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
}

// 页面加载时初始化
window.onload = initPage;