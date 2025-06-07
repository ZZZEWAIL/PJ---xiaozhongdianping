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
let bestCoupon = null;
let invitationCode = ''; // 邀请码
let isInvitationValid = false; // 邀请码是否有效

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
        displayCouponCards();
    } catch (err) {
        console.error('获取优惠券失败:', err);
        displayNoCoupons('无法加载优惠券，请稍后重试');
    }
}

/**
 * 展示套餐信息
 * @param {Object} packageData 套餐数据
 */
function displayPackageInfo(packageData) {
    const packageInfoContainer = document.getElementById('package-info');

    // 解析套餐内容
    const contentsList = parsePackageContents(packageData.contents);

    packageInfoContainer.innerHTML = `
        <div class="package-header">
            <h4 class="package-title">${packageData.title}</h4>
            <div class="package-price">¥${packageData.price.toFixed(2)}</div>
        </div>
        ${packageData.description ? `<p class="package-description">${packageData.description}</p>` : ''}
        <div class="package-contents">
            <h5 class="contents-title">套餐内容</h5>
            <ul class="contents-list">
                ${contentsList.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
        <div class="package-footer">
            <span class="package-sales">已售${packageData.sales}份</span>
        </div>
    `;
}

/**
 * 解析套餐内容字符串
 * @param {string} contents 套餐内容字符串，格式如 "汉堡*2+可乐*2"
 * @returns {string[]} 解析后的内容列表
 */
function parsePackageContents(contents) {
    if (!contents) return [];

    // 按+号分割不同项目
    return contents.split('+').map(item => {
        // 处理每个项目，格式如 "汉堡*2"
        const [name, quantity] = item.split('*');
        return quantity ? `${name.trim()} × ${quantity.trim()}` : name.trim();
    });
}

/**
 * 显示优惠券卡片
 */
function displayCouponCards() {
    const couponContainer = document.getElementById('coupon-container');
    
    // 如果没有可用优惠券
    if (!availableCoupons || availableCoupons.length === 0) {
        displayNoCoupons();
        return;
    }
    
    // 计算每个优惠券的优惠金额并排序
    if (packageData) {
        // 计算每个优惠券的优惠金额
        availableCoupons.forEach(couponInfo => {
            couponInfo.discountAmount = calculateDiscountAmount(packageData.price, couponInfo.coupon);
        });
        
        // 按优惠金额从高到低排序
        availableCoupons.sort((a, b) => b.discountAmount - a.discountAmount);
        
        // 标记最佳优惠券
        bestCoupon = availableCoupons[0];
    }
    
    // 清空容器
    couponContainer.innerHTML = '';
    
    // 添加"不使用优惠券"选项
    const noCouponCard = document.createElement('div');
    noCouponCard.className = 'coupon-card no-coupon';
    noCouponCard.dataset.couponId = '';
    noCouponCard.innerHTML = `
        <i class="bi bi-x-circle mb-2" style="font-size: 1.5rem; color: #6c757d;"></i>
        <div>不使用优惠券</div>
    `;
    couponContainer.appendChild(noCouponCard);
    
    // 添加所有可用优惠券
    availableCoupons.forEach(couponInfo => {
        const coupon = couponInfo.coupon;
        const isBest = couponInfo === bestCoupon;
        
        const card = document.createElement('div');
        card.className = `coupon-card ${isBest ? 'selected' : ''}`;
        card.dataset.couponId = couponInfo.id;
        card.dataset.coupon = JSON.stringify(couponInfo);
        
        card.innerHTML = `
            ${isBest ? '<div class="coupon-best-badge">最优惠</div>' : ''}
            <div class="coupon-name">${coupon.name}</div>
            <div class="coupon-discount">${formatCouponValue(coupon)}</div>
            <div class="coupon-description">${coupon.description || '无使用限制'}</div>
            <div class="coupon-expiry">有效期至 ${formatExpiryDate(couponInfo.expiry_date)}</div>
        `;
        
        couponContainer.appendChild(card);
    });
    
    // 设置初始选择的优惠券
    if (bestCoupon) {
        selectedCoupon = bestCoupon;
        updateCouponDetails(bestCoupon);
    }
    
    // 更新金额显示
    updateOrderAmount();
    
    // 添加点击事件
    attachCouponEvents();
}

/**
 * 显示没有可用优惠券的提示
 * @param {string} message 显示消息
 */
function displayNoCoupons(message = '暂无可用优惠券') {
    const couponContainer = document.getElementById('coupon-container');
    
    // 清空容器
    couponContainer.innerHTML = '';
    
    // 添加"不使用优惠券"选项
    const noCouponCard = document.createElement('div');
    noCouponCard.className = 'coupon-card no-coupon selected';
    noCouponCard.dataset.couponId = '';
    noCouponCard.innerHTML = `
        <i class="bi bi-x-circle mb-2" style="font-size: 1.5rem; color: #6c757d;"></i>
        <div>不使用优惠券</div>
    `;
    couponContainer.appendChild(noCouponCard);
    
    // 添加无优惠券提示
    const noAvailableCard = document.createElement('div');
    noAvailableCard.className = 'coupon-card no-coupon';
    noAvailableCard.style.backgroundColor = '#f8f9fa';
    noAvailableCard.style.cursor = 'default';
    noAvailableCard.innerHTML = `
        <i class="bi bi-info-circle mb-2" style="font-size: 1.5rem; color: #6c757d;"></i>
        <div>${message}</div>
    `;
    couponContainer.appendChild(noAvailableCard);
    
    // 添加点击事件
    attachCouponEvents();
}

/**
 * 为优惠券卡片添加点击事件
 */
function attachCouponEvents() {
    const couponCards = document.querySelectorAll('.coupon-card');
    
    couponCards.forEach(card => {
        card.addEventListener('click', () => {
            // 如果未启用优惠券，不处理点击
            const useCouponCheckbox = document.getElementById('use-coupon');
            if (!useCouponCheckbox.checked) return;
            
            // 如果是无法选择的卡片（比如提示卡片），不处理点击
            if (card.style.cursor === 'default') return;
            
            // 移除之前的选择
            document.querySelectorAll('.coupon-card.selected').forEach(selected => {
                selected.classList.remove('selected');
            });
            
            // 添加选中样式
            card.classList.add('selected');
            
            // 设置选中的优惠券
            const couponId = card.dataset.couponId;
            if (couponId) {
                selectedCoupon = JSON.parse(card.dataset.coupon);
                updateCouponDetails(selectedCoupon);
            } else {
                selectedCoupon = null;
                document.getElementById('coupon-details').classList.add('d-none');
            }
            
            // 更新订单金额
            updateOrderAmount();
        });
    });
}

/**
 * 更新所选优惠券详情显示
 * @param {Object} couponInfo 优惠券信息
 */
function updateCouponDetails(couponInfo) {
    const detailsContainer = document.getElementById('coupon-details');
    const coupon = couponInfo.coupon;
    
    detailsContainer.innerHTML = `
        <div><strong>${coupon.name}</strong> - ${formatCouponValue(coupon)}</div>
        <div>${coupon.description || '无使用限制'}</div>
        <div>优惠金额: ¥${calculateDiscountAmount(packageData.price, coupon).toFixed(2)}</div>
        <div>有效期至: ${formatExpiryDate(couponInfo.expiry_date)}</div>
    `;
    
    detailsContainer.classList.remove('d-none');
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
            let display = `减至${coupon.discount_value}元`;
            if (coupon.max_discount) {
                display += `，最高减${coupon.max_discount}元`;
            }
            return display;
        case 'discount':
            let discountDisplay = `${coupon.discount_value * 10}折`;
            if (coupon.max_discount) {
                discountDisplay += `，最高减${coupon.max_discount}元`;
            }
            return discountDisplay;
        default:
            return '未知类型';
    }
}

/**
 * 格式化过期日期
 * @param {string} dateString 日期字符串
 * @returns {string} 格式化后的日期
 */
function formatExpiryDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

/**
 * 计算优惠券折扣金额
 * @param {number} originalPrice 原价
 * @param {Object} coupon 优惠券数据
 * @returns {number} 折扣金额
 */
function calculateDiscountAmount(originalPrice, coupon) {
    let finalPrice = originalPrice;
    let discountAmount = 0;
    
    switch (coupon.discount_type) {
        case 'deduction':
            // 固定金额减免
            finalPrice = originalPrice - coupon.discount_value;
            if (finalPrice < 0) finalPrice = 0;
            discountAmount = originalPrice - finalPrice;
            break;
            
        case 'fixed_amount':
            // 减至固定金额（例如：减至0.1元券），考虑最大优惠限制
            const potentialDiscount = originalPrice - coupon.discount_value;
            // 如果原价低于固定金额，则不打折
            if (originalPrice <= coupon.discount_value) {
                discountAmount = 0;
            } else {
                // 检查是否有最大优惠限制
                if (coupon.max_discount && potentialDiscount > coupon.max_discount) {
                    discountAmount = coupon.max_discount;
                } else {
                    discountAmount = potentialDiscount;
                }
            }
            finalPrice = originalPrice - discountAmount;
            break;
            
        case 'discount':
            // 折扣比例
            finalPrice = originalPrice * coupon.discount_value;
            // 检查是否有最大优惠限制
            if (coupon.max_discount) {
                const fullDiscount = originalPrice - finalPrice;
                if (fullDiscount > coupon.max_discount) {
                    finalPrice = originalPrice - coupon.max_discount;
                }
            }
            // 四舍五入保留两位小数
            finalPrice = Math.round(finalPrice * 100) / 100;
            discountAmount = originalPrice - finalPrice;
            break;
            
        default:
            discountAmount = 0;
    }
    
    return discountAmount;
}

/**
 * 更新订单金额显示
 */
function updateOrderAmount() {
    if (!packageData) return;

    const originalPrice = packageData.price;
    let discountAmount = 0;

    // 计算优惠金额
    if (selectedCoupon && document.getElementById('use-coupon').checked) {
        discountAmount = calculateDiscountAmount(originalPrice, selectedCoupon.coupon);
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
    
    useCouponCheckbox.addEventListener('change', () => {
        const couponContainer = document.getElementById('coupon-container');
        couponContainer.style.opacity = useCouponCheckbox.checked ? '1' : '0.5';
        couponContainer.style.pointerEvents = useCouponCheckbox.checked ? 'auto' : 'none';
        
        if (!useCouponCheckbox.checked) {
            document.getElementById('coupon-details').classList.add('d-none');
        } else if (selectedCoupon) {
            document.getElementById('coupon-details').classList.remove('d-none');
        }
        
        updateOrderAmount();
    });

    // 邀请码相关事件绑定
    bindInvitationEvents();

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
 * 绑定邀请码相关事件
 */
function bindInvitationEvents() {
    const invitationInput = document.getElementById('invitation-code-input');
    const clearBtn = document.getElementById('clear-invitation-btn');
    const useInvitationCheckbox = document.getElementById('use-invitation');

    // 邀请码输入框事件
    if (invitationInput) {
        // 输入时实时验证
        invitationInput.addEventListener('input', handleInvitationInput);
        
        // 失去焦点时验证
        invitationInput.addEventListener('blur', validateInvitationCode);
    }

    // 清除按钮
    if (clearBtn) {
        clearBtn.addEventListener('click', clearInvitationCode);
    }

    // 使用邀请码开关
    if (useInvitationCheckbox) {
        useInvitationCheckbox.addEventListener('change', handleInvitationToggle);
    }
}

/**
 * 处理邀请码输入
 * @param {Event} event - 输入事件
 */
function handleInvitationInput(event) {
    const input = event.target;
    let value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // 限制长度为6位
    if (value.length > 6) {
        value = value.substring(0, 6);
    }
    
    input.value = value;
    invitationCode = value;
    
    // 清除之前的验证状态
    clearInvitationStatus();
    
    // 如果输入完整6位，自动验证
    if (value.length === 6) {
        validateInvitationCode();
    } else if (value.length === 0) {
        isInvitationValid = false;
    }
}

/**
 * 验证邀请码
 */
async function validateInvitationCode() {
    const invitationInput = document.getElementById('invitation-code-input');
    const code = invitationInput.value.trim();
    
    if (!code || code.length !== 6) {
        clearInvitationStatus();
        isInvitationValid = false;
        return;
    }

    try {
        showInvitationLoading();
        
        // 调用后端接口验证邀请码
        const response = await fetch(`${API_BASE}/invitation/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ code })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '邀请码验证失败');
        }

        const result = await response.json();

        // 验证成功
        showInvitationSuccess();
        isInvitationValid = true;
        console.log('邀请码验证成功:', result);
        
    } catch (error) {
        console.error('邀请码验证失败:', error.message || error);
        showInvitationError(error.message || '邀请码验证失败');
        isInvitationValid = false;
    }
}

/**
 * 显示邀请码验证中状态
 */
function showInvitationLoading() {
    const statusDiv = document.getElementById('invitation-status');
    statusDiv.className = 'd-flex align-items-center text-info';
    statusDiv.innerHTML = `
        <div class="spinner-border spinner-border-sm me-2" role="status">
            <span class="visually-hidden">验证中...</span>
        </div>
        <small>正在验证邀请码...</small>
    `;
}

/**
 * 显示邀请码验证成功状态
 */
function showInvitationSuccess() {
    const statusDiv = document.getElementById('invitation-status');
    statusDiv.className = 'd-flex align-items-center text-success';
    statusDiv.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        <small>邀请码验证成功！使用此邀请码下单，邀请人可获得奖励</small>
    `;
}

/**
 * 显示邀请码验证错误状态
 * @param {string} message - 错误信息
 */
function showInvitationError(message) {
    const statusDiv = document.getElementById('invitation-status');
    statusDiv.className = 'd-flex align-items-center text-danger';
    statusDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <small>${escapeHtml(message)}</small>
    `;
}

/**
 * 清除邀请码验证状态
 */
function clearInvitationStatus() {
    const statusDiv = document.getElementById('invitation-status');
    statusDiv.className = 'd-none';
    statusDiv.innerHTML = '';
}

/**
 * 清除邀请码输入
 */
function clearInvitationCode() {
    const invitationInput = document.getElementById('invitation-code-input');
    invitationInput.value = '';
    invitationCode = '';
    isInvitationValid = false;
    clearInvitationStatus();
}

/**
 * 处理邀请码开关切换
 * @param {Event} event - 切换事件
 */
function handleInvitationToggle(event) {
    const isChecked = event.target.checked;
    const container = document.getElementById('invitation-input-container');
    
    if (!isChecked) {
        // 如果关闭邀请码功能，清除状态
        clearInvitationCode();
    }
}

/**
 * 提交订单
 */
async function submitOrder() {
    if (!packageData) {
        showError('订单信息不完整，请刷新页面重试');
        return;
    }

    // 验证邀请码
    const useInvitation = document.getElementById('use-invitation').checked;
    if (useInvitation && invitationCode) {
        if (!isInvitationValid) {
            showError('请先验证邀请码或取消使用邀请码');
            return;
        }
    }

    try {
        // 禁用按钮，防止重复提交
        const confirmBtn = document.getElementById('confirm-btn');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';

        // 构建订单数据
        const orderData = {
            package_id: packageData.id,
            coupon_id: selectedCoupon && document.getElementById('use-coupon').checked ? selectedCoupon.id : null
        };

        // 添加邀请码
        if (useInvitation && isInvitationValid && invitationCode) {
            orderData.invitation_code = invitationCode;
        }

        // 发送订单请求
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
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
        const modalBody = document.querySelector('#successModal .modal-body');
        let successContent = `
            <i class="bi bi-check-circle-fill text-success success-icon"></i>
            <p class="mt-3">订单已成功支付！</p>
            <p>订单号：${orderResult.id}</p>
            <p>券码：${orderResult.voucher_code}</p>
            <p>实付金额：¥${orderResult.order_amount.toFixed(2)}</p>
        `;

        // 如果使用了邀请码，显示相关信息
        if (useInvitation && isInvitationValid && invitationCode) {
            successContent += `
                <p class="text-success">
                    <i class="bi bi-gift me-1"></i>
                    已使用邀请码：${invitationCode}
                </p>
            `;
        }

        successContent += '<p>您可以在"我的订单"中查看订单详情</p>';
        modalBody.innerHTML = successContent;

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
 * HTML转义函数，防止XSS攻击
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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