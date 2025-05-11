/**
 * 订单确认页面脚本
 * 处理套餐详情展示、优惠券选择和订单提交
 */

// 从 URL 获取 package_id
const urlParams = new URLSearchParams(window.location.search);
const packageId = urlParams.get('package_id');
const API_BASE = "http://127.0.0.1:8000/api";

// 全局变量
let packageData = null;
let availableCoupons = [];
let selectedCoupon = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    if (!packageId) {
        showError('未找到套餐ID');
        return;
    }

    // 获取套餐详情
    fetchPackageDetail();

    // 获取用户可用优惠券
    fetchAvailableCoupons();

    // 绑定事件处理
    bindEvents();
});

/**
 * 获取套餐详情
 */
async function fetchPackageDetail() {
    try {
        const response = await fetch(`${API_BASE}/packages/${packageId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        packageData = await response.json();
        displayPackageInfo(packageData);
        updateOrderAmount();
    } catch (err) {
        console.error('获取套餐详情失败:', err);
        showError('无法加载套餐详情，请稍后重试');
    }
}

/**
 * 获取用户可用优惠券
 */
async function fetchAvailableCoupons() {
    try {
        const response = await fetch(`${API_BASE}/user/coupons/available?package_id=${packageId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        availableCoupons = await response.json();
        populateCouponSelect();
    } catch (err) {
        console.error('获取优惠券失败:', err);
        // 不显示错误，因为优惠券是可选的
    }
}

/**
 * 展示套餐信息
 * @param {Object} packageData 套餐数据
 */
function displayPackageInfo(packageData) {
    const packageInfoContainer = document.getElementById('package-info');

    packageInfoContainer.innerHTML = `
        <h4 class="package-title">${packageData.title}</h4>
        <p class="package-shop">${packageData.shop_name || '商家信息加载中...'}</p>
        <p class="package-contents">${packageData.contents}</p>
        <p class="package-sales">已售${packageData.sales}份</p>
    `;
}

/**
 * 填充优惠券下拉选择框
 */
function populateCouponSelect() {
    const couponSelect = document.getElementById('coupon-select');

    // 清空现有选项
    couponSelect.innerHTML = '<option value="">选择优惠券</option>';

    if (!availableCoupons || availableCoupons.length === 0) {
        couponSelect.innerHTML = '<option value="" disabled>暂无可用优惠券</option>';
        return;
    }

    // 添加优惠券选项
    availableCoupons.forEach(couponInfo => {
        const coupon = couponInfo.coupon;
        const option = document.createElement('option');
        option.value = couponInfo.id; // 使用 UserCoupon 的 ID
        option.textContent = `${coupon.name} (${formatCouponValue(coupon)})`;
        option.dataset.coupon = JSON.stringify(couponInfo);
        couponSelect.appendChild(option);
    });
}

/**
 * 格式化优惠券显示值
 * @param {Object} coupon 优惠券数据
 * @returns {string} 格式化后的优惠券值
 */
function formatCouponValue(coupon) {
    switch (coupon.discount_type) {
        case 'deduction':
            return `减${coupon.discount_value}元`;
        case 'fixed_amount':
            return `${coupon.discount_value}元内免单`;
        case 'discount':
            return `${coupon.discount_value * 10}折`;
        default:
            return '未知类型';
    }
}

/**
 * 更新订单金额显示
 */
function updateOrderAmount() {
    if (!packageData) return;

    const originalPrice = packageData.price;
    let discountAmount = 0;

    // 计算优惠金额
    if (selectedCoupon) {
        const coupon = selectedCoupon.coupon;
        switch (coupon.discount_type) {
            case 'deduction':
                discountAmount = coupon.discount_value;
                break;
            case 'fixed_amount':
                discountAmount = Math.min(originalPrice, coupon.discount_value);
                break;
            case 'discount':
                discountAmount = originalPrice * (1 - coupon.discount_value);
                break;
        }
    }

    // 更新显示
    document.getElementById('original-price').textContent = `¥${originalPrice.toFixed(2)}`;
    document.getElementById('discount-amount').textContent = `-¥${discountAmount.toFixed(2)}`;
    document.getElementById('final-price').textContent = `¥${(originalPrice - discountAmount).toFixed(2)}`;
}

/**
 * 绑定事件处理
 */
function bindEvents() {
    // 优惠券复选框
    const useCouponCheckbox = document.getElementById('use-coupon');
    const couponSelect = document.getElementById('coupon-select');

    useCouponCheckbox.addEventListener('change', () => {
        couponSelect.disabled = !useCouponCheckbox.checked;
        if (!useCouponCheckbox.checked) {
            selectedCoupon = null;
            couponSelect.value = '';
            updateOrderAmount();
        }
    });

    // 优惠券选择
    couponSelect.addEventListener('change', () => {
        const selectedOption = couponSelect.options[couponSelect.selectedIndex];
        if (selectedOption && selectedOption.dataset.coupon) {
            selectedCoupon = JSON.parse(selectedOption.dataset.coupon);
        } else {
            selectedCoupon = null;
        }
        updateOrderAmount();
    });

    // 取消按钮
    document.getElementById('cancel-btn').addEventListener('click', () => {
        window.history.back();
    });

    // 确认支付按钮
    document.getElementById('confirm-btn').addEventListener('click', submitOrder);

    // 查看订单按钮
    document.getElementById('view-order-btn').addEventListener('click', () => {
        window.location.href = 'my_orders.html';
    });
}

/**
 * 提交订单
 */
async function submitOrder() {
    if (!packageData) {
        showError('订单信息不完整，请刷新页面重试');
        return;
    }

    try {
        // 禁用按钮，防止重复提交
        const confirmBtn = document.getElementById('confirm-btn');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';

        // 构建订单数据
        const orderData = {
            package_id: packageData.id,
            coupon_id: selectedCoupon ? selectedCoupon.id : null
        };

        // 发送订单请求
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '订单提交失败');
        }

        const orderResult = await response.json();

        // 显示成功模态框
        const successModal = new bootstrap.Modal(document.getElementById('successModal'));
        successModal.show();

        // 更新成功模态框中的订单信息
        document.querySelector('#successModal .modal-body').innerHTML = `
            <i class="bi bi-check-circle-fill text-success success-icon"></i>
            <p class="mt-3">订单已成功支付！</p>
            <p>订单号：${orderResult.id}</p>
            <p>券码：${orderResult.voucher_code}</p>
            <p>实付金额：¥${orderResult.order_amount.toFixed(2)}</p>
            <p>您可以在"我的订单"中查看订单详情</p>
        `;
    } catch (err) {
        console.error('提交订单失败:', err);
        showError(err.message || '订单提交失败，请稍后重试');

        // 恢复按钮状态
        const confirmBtn = document.getElementById('confirm-btn');
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> 确认支付';
    }
}

/**
 * 显示错误信息
 * @param {string} message 错误信息
 */
function showError(message) {
    // 创建错误提示元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.role = 'alert';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // 插入到页面顶部
    const container = document.querySelector('.container');
    container.insertBefore(errorDiv, container.firstChild);

    // 5秒后自动消失
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}