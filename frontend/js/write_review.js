/**
 * 写点评页面 JavaScript
 * 处理点评撰写、表单验证、字符计数、历史记录等功能
 * 
 * @author Frontend Team
 * @version 1.0
 */

const API_BASE = "http://127.0.0.1:8000/api";

// 获取URL参数
const urlParams = new URLSearchParams(window.location.search);
const shopId = urlParams.get('shop_id');

// 页面数据
let shopData = null;
let userReviews = [];
let isSubmitting = false;

/**
 * 页面加载完成后执行初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Write review page loaded');
    
    // 检查商家ID
    if (!shopId) {
        showError('缺少商家ID参数');
        setTimeout(() => {
            window.location.href = 'search.html';
        }, 2000);
        return;
    }
    
    // 初始化页面数据
    initializePage();
    
    // 绑定事件处理
    bindEvents();
});

/**
 * 初始化页面数据
 */
async function initializePage() {
    try {
        // 并行获取数据
        await Promise.all([
            fetchShopInfo(),
            fetchUserReviews()
        ]);
        
        console.log('Page initialized successfully');
    } catch (error) {
        console.error('Failed to initialize page:', error);
        showError('页面加载失败，请刷新重试');
    }
}

/**
 * 获取商家信息
 */
async function fetchShopInfo() {
    try {
        const response = await fetch(`${API_BASE}/shops/${shopId}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        shopData = data.shop;
        
        displayShopInfo(shopData);
        
    } catch (error) {
        console.error('Error fetching shop info:', error);
        displayShopInfoError();
    }
}

/**
 * 获取用户点评记录
 */
async function fetchUserReviews() {
    try {
        const response = await fetch(`${API_BASE}/user/reviews?limit=5`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        userReviews = data.reviews || [];
        
        displayUserReviews(userReviews, data.total || 0);
        
    } catch (error) {
        console.error('Error fetching user reviews:', error);
        displayUserReviewsError();
    }
}

/**
 * 显示商家信息
 * @param {Object} shop - 商家数据
 */
function displayShopInfo(shop) {
    const container = document.getElementById('shop-info');
    
    container.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="shop-avatar me-3">
                <i class="bi bi-shop" style="font-size: 2rem; color: #007bff;"></i>
            </div>
            <div class="shop-details">
                <h5 class="mb-1">${escapeHtml(shop.name)}</h5>
                <p class="mb-1 text-muted">
                    <i class="bi bi-geo-alt me-1"></i>
                    ${escapeHtml(shop.address)}
                </p>
                <div class="shop-meta">
                    <span class="badge bg-warning text-dark me-2">
                        <i class="bi bi-star-fill me-1"></i>
                        ${shop.rating}/5.0
                    </span>
                    <span class="text-muted">
                        <i class="bi bi-telephone me-1"></i>
                        ${escapeHtml(shop.phone)}
                    </span>
                </div>
            </div>
        </div>
        ${shop.description ? `
            <div class="shop-description mt-3 p-2 bg-light rounded">
                <small class="text-muted">${escapeHtml(shop.description)}</small>
            </div>
        ` : ''}
    `;
}

/**
 * 显示商家信息错误
 */
function displayShopInfoError() {
    const container = document.getElementById('shop-info');
    container.innerHTML = `
        <div class="text-center py-3 text-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>
            <span>无法加载商家信息</span>
            <button class="btn btn-outline-primary btn-sm ms-2" onclick="fetchShopInfo()">
                重试
            </button>
        </div>
    `;
}

/**
 * 显示用户点评记录
 * @param {Array} reviews - 点评列表
 * @param {number} total - 总数量
 */
function displayUserReviews(reviews, total) {
    const container = document.getElementById('my-reviews-list');
    const countBadge = document.getElementById('my-review-count');
    
    countBadge.textContent = `${total} 条点评`;
    
    if (reviews.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-chat-left-text text-muted" style="font-size: 3rem;"></i>
                <div class="mt-2 text-muted">您还没有写过点评</div>
                <small class="text-muted">写下您的第一条点评，帮助其他用户了解商家</small>
            </div>
        `;
        return;
    }
    
    const reviewsHtml = reviews.map(review => `
        <div class="review-history-item mb-3 p-3 border rounded">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div class="review-meta">
                    <small class="text-muted">
                        <i class="bi bi-clock me-1"></i>
                        ${formatDateTime(review.created_at)}
                    </small>
                </div>
                <span class="badge bg-primary">${review.content.length} 字</span>
            </div>
            <div class="review-content">
                <p class="mb-0">${escapeHtml(review.content)}</p>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `
        ${reviewsHtml}
        ${total > 5 ? `
            <div class="text-center mt-3">
                <small class="text-muted">
                    共 ${total} 条点评，仅显示最近 5 条
                </small>
            </div>
        ` : ''}
    `;
}

/**
 * 显示用户点评记录错误
 */
function displayUserReviewsError() {
    const container = document.getElementById('my-reviews-list');
    container.innerHTML = `
        <div class="text-center py-3 text-danger">
            <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
            <div class="mt-2">加载点评记录失败</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="fetchUserReviews()">
                重新加载
            </button>
        </div>
    `;
}

/**
 * 绑定事件处理
 */
function bindEvents() {
    // 点评内容输入框
    const reviewContent = document.getElementById('review-content');
    if (reviewContent) {
        reviewContent.addEventListener('input', handleContentInput);
        reviewContent.addEventListener('paste', handleContentPaste);
    }

    // 表单提交
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', handleFormSubmit);
    }

    // 取消按钮
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', handleCancel);
    }

    // 成功模态框按钮
    const viewShopBtn = document.getElementById('view-shop-btn');
    const continueReviewBtn = document.getElementById('continue-review-btn');
    
    if (viewShopBtn) {
        viewShopBtn.addEventListener('click', () => {
            window.location.href = `shops_detail.html?shop_id=${shopId}`;
        });
    }
    
    if (continueReviewBtn) {
        continueReviewBtn.addEventListener('click', () => {
            resetForm();
        });
    }
}

/**
 * 处理内容输入
 * @param {Event} event - 输入事件
 */
function handleContentInput(event) {
    updateCharacterCount();
    updateSubmitButton();
}

/**
 * 处理粘贴事件
 * @param {Event} event - 粘贴事件
 */
function handleContentPaste(event) {
    // 延迟执行以确保粘贴内容已插入
    setTimeout(() => {
        updateCharacterCount();
        updateSubmitButton();
    }, 10);
}

/**
 * 更新字符计数
 */
function updateCharacterCount() {
    const reviewContent = document.getElementById('review-content');
    const charCount = document.getElementById('char-count');
    const minIndicator = document.querySelector('.min-indicator');
    const statusText = minIndicator.querySelector('.status-text');
    
    const length = reviewContent.value.length;
    charCount.textContent = length;
    
    // 更新最少字符提示
    if (length < 15) {
        const remaining = 15 - length;
        statusText.textContent = `还需输入${remaining}字`;
        minIndicator.className = 'min-indicator ms-2 text-warning';
        minIndicator.querySelector('i').className = 'bi bi-exclamation-circle text-warning';
    } else {
        statusText.textContent = '字数满足要求';
        minIndicator.className = 'min-indicator ms-2 text-success';
        minIndicator.querySelector('i').className = 'bi bi-check-circle text-success';
    }
    
    // 更新字符计数颜色
    const charCountContainer = charCount.parentElement;
    if (length > 500) {
        charCountContainer.className = 'text-danger';
    } else if (length >= 15) {
        charCountContainer.className = 'text-success';
    } else {
        charCountContainer.className = 'text-muted';
    }
}

/**
 * 更新提交按钮状态
 */
function updateSubmitButton() {
    const reviewContent = document.getElementById('review-content');
    const submitBtn = document.getElementById('submit-btn');
    
    const length = reviewContent.value.trim().length;
    const isValid = length >= 15 && length <= 500;
    
    submitBtn.disabled = !isValid || isSubmitting;
    
    if (isValid && !isSubmitting) {
        submitBtn.className = 'btn btn-primary';
    } else {
        submitBtn.className = 'btn btn-secondary';
    }
}

/**
 * 处理表单提交
 * @param {Event} event - 提交事件
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (isSubmitting) {
        return;
    }
    
    const reviewContent = document.getElementById('review-content');
    const content = reviewContent.value.trim();
    
    // 验证内容
    if (content.length < 15) {
        showError('点评内容不能少于15个字符');
        return;
    }
    
    if (content.length > 500) {
        showError('点评内容不能超过500个字符');
        return;
    }
    
    await submitReview(content);
}

/**
 * 提交点评
 * @param {string} content - 点评内容
 */
async function submitReview(content) {
    try {
        isSubmitting = true;
        updateSubmitButton();
        
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>发布中...';
        
        const response = await fetch(`${API_BASE}/shops/${shopId}/reviews`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '点评提交失败');
        }
        
        const result = await response.json();
        
        // 显示成功模态框
        showSuccessModal(result);

        // 如果有奖励信息，显示奖励提示
        if (result.reward) {
            showSuccess(`恭喜您获得奖励券：${result.reward.coupon_name}，${result.reward.coupon_value}，有效期${result.reward.expiry_days}天`);
        }

        // 刷新用户点评记录
        await fetchUserReviews();
        
    } catch (error) {
        console.error('点评提交失败:', error);
        showError(error.message || '点评提交失败，请稍后重试');
        
    } finally {
        isSubmitting = false;
        updateSubmitButton();
        
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.innerHTML = '<i class="bi bi-send me-1"></i>发布点评';
    }
}

/**
 * 显示成功模态框
 * @param {Object} result - 提交结果
 */
function showSuccessModal(result) {
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
    const successContent = document.getElementById('success-content');
    
    let content = `
        <i class="bi bi-check-circle-fill text-success" style="font-size: 3rem;"></i>
        <h4 class="mt-3">点评发布成功！</h4>
        <p class="text-muted">感谢您分享宝贵的评价</p>
    `;
    
    // 如果有奖励信息，显示奖励提示
    if (result.reward) {
        content += `
            <div class="alert alert-success">
                <h5 class="alert-heading">
                    <i class="bi bi-gift me-2"></i>恭喜获得奖励！
                </h5>
                <p class="mb-1">您已完成3条有效点评，获得了：</p>
                <p class="mb-1"><strong>${result.reward.coupon_name}</strong></p>
                <p class="mb-1">${result.reward.coupon_value}</p>
                <small>优惠券已自动发放到您的卡包，${result.reward.expiry_days}天内有效</small>
            </div>
        `;
    }
    
    successContent.innerHTML = content;
    modal.show();
}

/**
 * 处理取消操作
 */
function handleCancel() {
    if (document.getElementById('review-content').value.trim()) {
        if (confirm('确定要放弃当前编辑的点评吗？')) {
            goBack();
        }
    } else {
        goBack();
    }
}

/**
 * 返回上一页
 */
function goBack() {
    if (document.referrer && document.referrer.includes('shops_detail.html')) {
        window.history.back();
    } else {
        window.location.href = `shops_detail.html?shop_id=${shopId}`;
    }
}

/**
 * 重置表单
 */
function resetForm() {
    const reviewContent = document.getElementById('review-content');
    reviewContent.value = '';
    updateCharacterCount();
    updateSubmitButton();
    reviewContent.focus();
}

/**
 * 格式化日期时间
 * @param {string} dateString - ISO格式日期字符串
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '未知时间';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('Date formatting error:', error);
        return '时间格式错误';
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
 * 显示成功信息
 * @param {string} message - 成功消息
 */
function showSuccess(message) {
    // 创建成功提示
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.role = 'alert';
    successDiv.innerHTML = `
        <i class="bi bi-check-circle me-1"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // 插入到页面顶部
    const container = document.querySelector('.container');
    container.insertBefore(successDiv, container.firstChild);

    // 3秒后自动消失
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showError(message) {
    // 创建错误提示元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.role = 'alert';
    errorDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle me-1"></i>
        ${escapeHtml(message)}
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