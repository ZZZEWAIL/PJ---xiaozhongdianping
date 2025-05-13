/**
 * 我的卡包 - 优惠券管理页面
 * 
 * 此JS文件处理:
 * 1. 从后端获取当前用户的优惠券列表
 * 2. 按状态(未使用/已使用/已过期)渲染优惠券
 * 3. 展示优惠券详细信息(折扣金额、使用限制、有效期等)
 */

// API URL
const API_BASE_URL = '/api';

// DOM 元素
const unusedContainer = document.getElementById('unused-container');
const usedContainer = document.getElementById('used-container');
const expiredContainer = document.getElementById('expired-container');

const unusedList = document.getElementById('unused-list');
const usedList = document.getElementById('used-list');
const expiredList = document.getElementById('expired-list');

const unusedLoading = document.getElementById('unused-loading');
const usedLoading = document.getElementById('used-loading');
const expiredLoading = document.getElementById('expired-loading');

const unusedEmpty = document.getElementById('unused-empty');
const usedEmpty = document.getElementById('used-empty');
const expiredEmpty = document.getElementById('expired-empty');

const unusedCount = document.getElementById('unused-count');
const usedCount = document.getElementById('used-count');
const expiredCount = document.getElementById('expired-count');

const getCouponsBtn = document.getElementById('get-coupons-btn');

/**
 * 初始化页面
 */
document.addEventListener('DOMContentLoaded', async() => {

    try {
        // 获取优惠券数据
        await fetchCoupons();

        // 绑定事件监听
        if (getCouponsBtn) {
            getCouponsBtn.addEventListener('click', () => {
                // 跳转到商品页面或领券中心
                window.location.href = 'search.html';
            });
        }
    } catch (error) {
        console.error('初始化失败:', error);
        showErrorMessage('加载优惠券时出错，请稍后重试');
    }
});

/**
 * 获取用户所有优惠券
 */
async function fetchCoupons() {
    try {
        // 显示加载动画
        showLoading(true);

        // 发起API请求
        const response = await fetch(`${API_BASE_URL}/user/coupons`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        });

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }

        // 解析数据
        const data = await response.json();

        // 渲染优惠券
        renderCoupons(data);
    } catch (error) {
        console.error('获取优惠券失败:', error);
        showErrorMessage('加载优惠券数据失败');
    } finally {
        // 隐藏加载动画
        showLoading(false);
    }
}

/**
 * 渲染优惠券列表
 * @param {Object} data - 包含三种状态优惠券的数据对象 {unused, used, expired}
 */
function renderCoupons(data) {
    // 更新计数
    unusedCount.textContent = data.unused.length;
    usedCount.textContent = data.used.length;
    expiredCount.textContent = data.expired.length;

    // 渲染每种状态的优惠券
    renderCouponsByType(data.unused, unusedList, unusedEmpty, 'unused');
    renderCouponsByType(data.used, usedList, usedEmpty, 'used');
    renderCouponsByType(data.expired, expiredList, expiredEmpty, 'expired');
}

/**
 * 按状态渲染优惠券
 * @param {Array} coupons - 优惠券数组
 * @param {HTMLElement} listElement - 列表容器元素
 * @param {HTMLElement} emptyElement - 空状态提示元素
 * @param {string} type - 优惠券类型 (unused/used/expired)
 */
function renderCouponsByType(coupons, listElement, emptyElement, type) {
    // 清空列表
    listElement.innerHTML = '';

    // 检查是否有优惠券
    if (coupons.length === 0) {
        // 显示空状态提示
        emptyElement.classList.remove('d-none');
        return;
    }

    // 隐藏空状态提示
    emptyElement.classList.add('d-none');

    // 按优惠券排序
    const sortedCoupons = [...coupons].sort((a, b) => {
        // 未使用券按到期时间升序
        if (type === 'unused' && a.expires_at && b.expires_at) {
            return new Date(a.expires_at) - new Date(b.expires_at);
        }
        // 已使用和已过期券按ID降序
        return b.id - a.id;
    });

    // 遍历优惠券并渲染
    sortedCoupons.forEach(coupon => {
        const couponElement = createCouponElement(coupon, type);
        listElement.appendChild(couponElement);
    });
}

/**
 * 创建单个优惠券元素
 * @param {Object} couponData - 优惠券数据
 * @param {string} type - 优惠券类型 (unused/used/expired)
 * @returns {HTMLElement} 优惠券DOM元素
 */
function createCouponElement(couponData, type) {
    const { coupon, expires_at } = couponData;

    // 创建列容器
    const colElement = document.createElement('div');
    colElement.className = 'col-md-6 col-lg-4';

    // 格式化优惠券数据
    const discountText = formatDiscountText(coupon);
    const expiryText = formatExpiryDate(expires_at);
    const daysLeft = type === 'unused' ? calculateDaysLeft(expires_at) : null;

    // 组装优惠券HTML
    colElement.innerHTML = `
        <div class="coupon-card ${type}">
            ${type !== 'unused' ? `<div class="status-badge">${type === 'used' ? '已使用' : '已过期'}</div>` : ''}
            <div class="discount-type">${getDiscountTypeText(coupon.discount_type)}</div>
            <div class="coupon-value">
                <h3>${discountText}</h3>
                <p>${coupon.name}</p>
            </div>
            <div class="coupon-info">
                <div class="coupon-title">${coupon.description || coupon.name}</div>
                
                ${coupon.min_spend > 0 ? `
                <div class="coupon-restriction">
                    <i class="bi bi-info-circle"></i> 
                    满${coupon.min_spend}元可用
                </div>` : ''}
                
                ${coupon.category ? `
                <div class="coupon-restriction">
                    <i class="bi bi-tag"></i> 
                    仅限${coupon.category}类别
                </div>` : ''}
                
                ${coupon.shop_restriction ? `
                <div class="coupon-restriction">
                    <i class="bi bi-shop"></i> 
                    仅限${coupon.shop_restriction}使用
                </div>` : ''}
                
                <div class="coupon-expiry">
                    <span class="expiry-text">有效期至：</span>
                    <span class="expiry-date">${expiryText}</span>
                    ${daysLeft !== null && daysLeft <= 3 ? `
                    <span class="days-left">剩${daysLeft}天</span>` : ''}
                </div>
            </div>
        </div>
    `;
    
    return colElement;
}

/**
 * 格式化优惠券折扣文本
 * @param {Object} coupon - 优惠券基本信息
 * @returns {string} 格式化后的折扣文本
 */
function formatDiscountText(coupon) {
    const { discount_type, discount_value, max_discount } = coupon;
    
    // 根据折扣类型返回不同文本
    switch (discount_type) {
        case 'percentage':
            return `${discount_value}折${max_discount ? `<span style="font-size: 12px;">最高减${max_discount}元</span>` : ''}`;
        case 'deduction':
            return `¥${discount_value.toFixed(1)}`;
        default:
            return `¥${discount_value.toFixed(1)}`;
    }
}

/**
 * 获取折扣类型文本
 * @param {string} type - 折扣类型
 * @returns {string} 对应的中文描述
 */
function getDiscountTypeText(type) {
    const typeMap = {
        'percentage': '折扣券',
        'deduction': '满减券'
    };
    return typeMap[type] || '优惠券';
}

/**
 * 格式化到期时间
 * @param {string} expiryDate - ISO格式的日期字符串
 * @returns {string} 格式化后的日期字符串
 */
function formatExpiryDate(expiryDate) {
    if (!expiryDate) return '永久有效';
    
    const date = new Date(expiryDate);
    return `${date.getFullYear()}-${padZero(date.getMonth() + 1)}-${padZero(date.getDate())}`;
}

/**
 * 计算剩余天数
 * @param {string} expiryDate - ISO格式的日期字符串
 * @returns {number|null} 剩余天数或null
 */
function calculateDaysLeft(expiryDate) {
    if (!expiryDate) return null;
    
    const expiry = new Date(expiryDate);
    const today = new Date();
    
    // 设置时间为当天23:59:59
    expiry.setHours(23, 59, 59, 999);
    today.setHours(0, 0, 0, 0);
    
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
}

/**
 * 数字补零
 * @param {number} num - 数字
 * @returns {string} 补零后的字符串
 */
function padZero(num) {
    return num < 10 ? `0${num}` : `${num}`;
}

/**
 * 控制加载动画的显示和隐藏
 * @param {boolean} show - 是否显示加载动画
 */
function showLoading(show) {
    if (show) {
        unusedLoading.classList.remove('d-none');
        usedLoading.classList.remove('d-none');
        expiredLoading.classList.remove('d-none');
    } else {
        unusedLoading.classList.add('d-none');
        usedLoading.classList.add('d-none');
        expiredLoading.classList.add('d-none');
    }
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showErrorMessage(message) {
    // 简单实现：可以使用弹窗或页内提示
    alert(message);
}