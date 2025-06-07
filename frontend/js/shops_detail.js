/**
 * 商家详情页面脚本
 * 处理商家信息展示、套餐列表、点评显示和回复功能
 * 
 * @author Frontend Team
 * @version 1.0
 */

// 从 URL 获取 shop_id
const urlParams = new URLSearchParams(window.location.search);
const shopId = urlParams.get('shop_id');
const API_BASE = "http://127.0.0.1:8000/api";

// 全局变量
let currentImagePage = 1;
const imagePageSize = 1; // 每页显示 1 张图片
let currentReviewPage = 1;
let currentSort = 'newest';
let allReviews = [];

/**
 * 页面加载完成后执行初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    if (!shopId) {
        alert('未找到商家 ID');
        window.location.href = 'search.html';
        return;
    }

    // 初始化页面数据
    fetchShopDetail();
    fetchPackages();
    fetchShopReviews();
    
    // 绑定事件处理
    bindEvents();
});

/**
 * 获取并展示商家详情
 */
async function fetchShopDetail() {
    try {
        const response = await fetch(`${API_BASE}/shops/${shopId}?image_page=${currentImagePage}&image_page_size=${imagePageSize}`, {
            method: 'GET',
            credentials: 'include', // 确保请求携带 Cookie
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displayShopDetail(data);
    } catch (err) {
        console.error('Fetch shop detail error:', err);
        showError('无法加载商家详情，请稍后重试');
    }
}

/**
 * 展示商家详情和图片
 * @param {Object} data - 商家数据
 */
function displayShopDetail(data) {
    const shopDetailContainer = document.getElementById('shop-detail');
    const imageContainer = document.getElementById('image-container');
    const imagePageInfo = document.getElementById('image-page-info');
    const prevButton = document.getElementById('prev-image');
    const nextButton = document.getElementById('next-image');

    // 展示商家信息
    const shop = data.shop;
    shopDetailContainer.innerHTML = `
        <h3>${escapeHtml(shop.name)}</h3>
        <p><strong>地址:</strong> ${escapeHtml(shop.address)}</p>
        <p><strong>电话:</strong> ${escapeHtml(shop.phone)}</p>
        <p><strong>评分:</strong> ${shop.rating}/5.0 ⭐</p>
        <p><strong>简介:</strong> ${escapeHtml(shop.description)}</p>
        ${shop.image_url ? `<img src="${shop.image_url}" alt="${escapeHtml(shop.name)}" style="max-width: 100%; border-radius: 8px; margin-top: 10px;">` : ''}
    `;

    // 展示图片
    const images = data.images;
    if (images.data && images.data.length > 0) {
        imageContainer.innerHTML = `<img src="${images.data[0].image_url}" alt="Shop Image">`;
    } else {
        imageContainer.innerHTML = '<p class="text-muted">暂无图片</p>';
    }

    // 更新分页信息
    const totalPages = Math.ceil((images.total || 0) / (images.page_size || 1));
    imagePageInfo.textContent = `第 ${images.page || 1} 页 / 共 ${totalPages} 页`;

    // 控制分页按钮
    prevButton.disabled = (images.page || 1) <= 1;
    nextButton.disabled = (images.page || 1) >= totalPages;

    // 更新全局分页参数
    currentImagePage = images.page || 1;
}

/**
 * 获取店铺的团购套餐列表
 */
async function fetchPackages() {
    try {
        const packagesContainer = document.getElementById('packages-container');
        
        const response = await fetch(`${API_BASE}/shops/${shopId}/packages`, {
            method: 'GET',
            credentials: 'include', // 确保请求携带 Cookie
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const packages = await response.json();
        
        // 移除加载指示器
        const loadingElements = packagesContainer.querySelectorAll('.loading-container');
        loadingElements.forEach(el => el.remove());
        
        displayPackages(packages);
    } catch (err) {
        console.error('获取套餐列表失败:', err);
        const packagesContainer = document.getElementById('packages-container');
        packagesContainer.innerHTML = `
            <div class="col-12 text-center">
                <p class="text-danger">获取套餐失败，请稍后重试</p>
            </div>
        `;
    }
}

/**
 * 展示团购套餐列表
 * @param {Array} packages - 套餐列表数据
 */
function displayPackages(packages) {
    const packagesContainer = document.getElementById('packages-container');
    
    if (!packages || packages.length === 0) {
        packagesContainer.innerHTML = `
            <div class="col-12 text-center">
                <p class="text-muted">暂无套餐</p>
            </div>
        `;
        return;
    }
    
    let packagesHTML = '';
    
    packages.forEach(pkg => {
        packagesHTML += `
            <div class="col">
                <div class="card package-card h-100" data-package-id="${pkg.id}">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHtml(pkg.title)}</h5>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="price">¥${pkg.price.toFixed(2)}</span>
                            <span class="sales-badge">已售${pkg.sales}份</span>
                        </div>
                        <p class="card-text content-preview">${escapeHtml(pkg.contents)}</p>
                        ${pkg.description ? `<p class="card-text"><small class="text-muted">${escapeHtml(pkg.description)}</small></p>` : ''}
                    </div>
                    <div class="card-footer bg-transparent text-center">
                        <button class="btn btn-outline-primary view-detail-btn">立即购买</button>
                    </div>
                </div>
            </div>
        `;
    });
    
    packagesContainer.innerHTML = packagesHTML;
    
    // 添加点击事件处理
    document.querySelectorAll('.package-card').forEach(card => {
        card.addEventListener('click', () => {
            const packageId = card.getAttribute('data-package-id');
            window.location.href = `order_confirm.html?package_id=${packageId}`;
        });
    });
}

/**
 * 获取商家点评列表
 * @param {number} page - 页码
 * @param {string} sort - 排序方式
 */
async function fetchShopReviews(page = 1, sort = 'newest') {
    try {
        const response = await fetch(`${API_BASE}/shops/${shopId}/reviews?page=${page}&limit=10&sort=${sort}`, {
            method: 'GET',
            credentials: 'include', // 确保请求携带 Cookie
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Fetched reviews data:', data); // 打印后端返回的数据

        if (!data || !Array.isArray(data)) {
            throw new Error('Invalid reviews data');
        }
        
        if (page === 1) {
            allReviews = data;
        } else {
            allReviews = allReviews.concat(data);
        }

        console.log('Fetched reviews data:', allReviews); // 打印后端返回的数据
        
        displayReviews(allReviews);
        updateReviewControls(data);
        
        currentReviewPage = page;
        currentSort = sort;
        
    } catch (err) {
        console.error('获取点评失败:', err);
        displayReviewsError();
    }
}

/**
 * 显示点评列表
 * @param {Array} reviews - 点评数据
 */
function displayReviews(reviews) {
    const container = document.getElementById('reviews-container');
    const countBadge = document.getElementById('review-count');
    
    countBadge.textContent = reviews.length;
    
    if (reviews.length === 0) {
        container.innerHTML = `
            <div class="reviews-empty">
                <i class="bi bi-chat-left-text"></i>
                <div>暂无点评</div>
                <small class="text-muted">成为第一个评价此商家的用户吧！</small>
            </div>
        `;
        return;
    }
    
    const reviewsHtml = reviews.map(review => generateReviewHtml(review)).join('');
    container.innerHTML = reviewsHtml;
    
    // 绑定回复按钮事件
    bindReplyEvents();
}

/**
 * 生成单个点评的HTML
 * @param {Object} review - 点评数据
 * @param {number} level - 嵌套层级
 * @returns {string} HTML字符串
 */
function generateReviewHtml(review, level = 0) {
    console.log('Generating HTML for review:', review); // 添加调试日志

    const levelClass = level > 0 ? `reply-item level-${Math.min(level, 4)}` : '';
    const maxLevel = level >= 4 ? 'level-max' : '';
    const username = review.username || "未知用户"; // 使用后端返回的 username
    
    let html = `
        <div class="review-item ${levelClass} ${maxLevel}" data-review-id="${review.id}">
            ${level > 0 ? '<div class="reply-indicator"></div>' : ''}
            <div class="review-header">
                <div class="review-author">
                    <div class="avatar">${username.charAt(0).toUpperCase()}</div>
                    <span class="username">${escapeHtml(username)}</span>
                    <span class="review-time">${formatDateTime(review.created_at)}</span>
                </div>
            </div>
            <div class="review-content">
                <p>${escapeHtml(review.content)}</p>
            </div>
            <div class="review-actions">
                <div class="action-buttons">
                    <button class="btn btn-sm reply-btn" data-review-id="${review.id}" data-username="${escapeHtml(review.username)}">
                        <i class="bi bi-reply me-1"></i>回复
                    </button>
                </div>
                ${review.replies && review.replies.length > 0 ? `<div class="reply-count">${review.replies.length} 条回复</div>` : ''}
            </div>
        </div>
    `;
    
    // 递归添加回复
    if (review.replies && review.replies.length > 0) {
        review.replies.forEach(reply => {
            html += generateReviewHtml(reply, level + 1);
        });
    }
    
    return html;
}

/**
 * 显示点评错误状态
 */
function displayReviewsError() {
    const container = document.getElementById('reviews-container');
    container.innerHTML = `
        <div class="text-center py-4 text-danger">
            <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
            <div class="mt-2">加载点评失败</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="fetchShopReviews()">
                重新加载
            </button>
        </div>
    `;
}

/**
 * 更新点评控制按钮状态
 * @param {Object} data - 点评数据
 */
function updateReviewControls(data) {
    const loadMoreBtn = document.getElementById('load-more-reviews');
    
    if (data.has_more) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

/**
 * 绑定事件处理
 */
function bindEvents() {
    // 图片分页按钮
    document.getElementById('prev-image').addEventListener('click', () => {
        if (currentImagePage > 1) {
            currentImagePage--;
            fetchShopDetail();
        }
    });

    document.getElementById('next-image').addEventListener('click', () => {
        currentImagePage++;
        fetchShopDetail();
    });

    // 写点评按钮
    const writeReviewBtn = document.getElementById('write-review-btn');
    if (writeReviewBtn) {
        writeReviewBtn.addEventListener('click', () => {
            window.location.href = `write_review.html?shop_id=${shopId}`;
        });
    }

    // 点评排序
    const sortRadios = document.querySelectorAll('input[name="review-sort"]');
    sortRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                allReviews = [];
                currentReviewPage = 1;
                fetchShopReviews(1, e.target.value);
            }
        });
    });

    // 加载更多点评
    const loadMoreBtn = document.getElementById('load-more-reviews');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            fetchShopReviews(currentReviewPage + 1, currentSort);
        });
    }

    // 回复模态框事件
    bindReplyModalEvents();
}

/**
 * 绑定回复相关事件
 */
function bindReplyEvents() {
    const replyBtns = document.querySelectorAll('.reply-btn');
    replyBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const reviewId = e.target.getAttribute('data-review-id');
            const username = e.target.getAttribute('data-username');
            showReplyModal(reviewId, username);
        });
    });
}

/**
 * 显示回复模态框
 * @param {string} reviewId - 点评ID
 * @param {string} username - 被回复用户名
 */
function showReplyModal(reviewId, username) {
    const modal = new bootstrap.Modal(document.getElementById('replyModal'));
    const targetInfo = document.getElementById('reply-target-info');
    const submitBtn = document.getElementById('submit-reply-btn');
    
    targetInfo.innerHTML = `
        <div class="alert alert-info mb-0">
            <i class="bi bi-reply me-1"></i>
            回复 <strong>${escapeHtml(username)}</strong> 的评论
        </div>
    `;
    
    // 清空回复内容
    document.getElementById('reply-content').value = '';
    updateReplyCharCount();
    
    // 设置提交按钮事件
    submitBtn.onclick = () => submitReply(reviewId);
    
    modal.show();
}

/**
 * 绑定回复模态框事件
 */
function bindReplyModalEvents() {
    const replyContent = document.getElementById('reply-content');
    const submitBtn = document.getElementById('submit-reply-btn');
    
    if (replyContent) {
        replyContent.addEventListener('input', updateReplyCharCount);
    }
}

/**
 * 更新回复字符计数
 */
function updateReplyCharCount() {
    const replyContent = document.getElementById('reply-content');
    const charCount = document.getElementById('reply-char-count');
    const submitBtn = document.getElementById('submit-reply-btn');
    
    const length = replyContent.value.length;
    charCount.textContent = length;
    
    if (length >= 1) {
        charCount.parentElement.classList.remove('text-danger');
        charCount.parentElement.classList.add('text-success');
        submitBtn.disabled = false;
    } else {
        charCount.parentElement.classList.remove('text-success');
        charCount.parentElement.classList.add('text-danger');
        submitBtn.disabled = true;
    }
}

/**
 * 提交回复
 * @param {string} reviewId - 点评ID
 */
async function submitReply(reviewId) {
    const replyContent = document.getElementById('reply-content');
    const content = replyContent.value.trim();
    
    if (content.length < 1) {
        showError('回复内容不能为空');
        return;
    }
    
    try {
        const submitBtn = document.getElementById('submit-reply-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>发布中...';
        
        const response = await fetch(`${API_BASE}/reviews/${reviewId}/reply`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '回复发布失败');
        }
        
        const result = await response.json();
        console.log('Fetched reply data:', result);
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('replyModal'));
        modal.hide();
        
        // 刷新点评列表
        allReviews = [];
        currentReviewPage = 1;
        await fetchShopReviews(1, currentSort);
        
        showSuccess('回复发布成功！');
        
    } catch (error) {
        console.error('回复发布失败:', error);
        showError(error.message || '回复发布失败，请稍后重试');
        
        // 恢复按钮状态
        const submitBtn = document.getElementById('submit-reply-btn');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '发布回复';
    }
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