/**
 * 我的邀请页面 JavaScript
 * 处理邀请码显示、邀请记录展示、奖励券明细等功能
 * 
 * @author Frontend Team
 * @version 1.0
 */

const API_BASE = "http://127.0.0.1:8000/api";

// 页面数据
let invitationCode = '';
let invitationRecords = [];
let rewardCoupons = [];

/**
 * 页面加载完成后执行初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('My invitation page loaded');
    
    // 初始化页面数据
    initializePage();
    
    // 绑定事件处理
    bindEvents();
});

/**
 * 初始化页面数据
 * 获取用户邀请码、邀请记录和奖励券信息
 */
async function initializePage() {
    try {
        // 并行获取数据以提高性能
        await Promise.all([
            fetchInvitationCode(),
            fetchInvitationRecords(),
            fetchRewardCoupons()
        ]);
        
        console.log('All invitation data loaded successfully');
    } catch (error) {
        console.error('Failed to initialize invitation page:', error);
        showError('页面加载失败，请刷新重试');
    }
}

/**
 * 获取用户邀请码
 * API: GET /api/invitation/code
 */
async function fetchInvitationCode() {
    try {
        const response = await fetch(`${API_BASE}/invitation/code`, {
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
        invitationCode = data.code || '';
        
        displayInvitationCode(invitationCode);
        
    } catch (error) {
        console.error('Error fetching invitation code:', error);
        displayInvitationCodeError();
    }
}

/**
 * 获取邀请记录
 * API: GET /api/invitation/records
 */
async function fetchInvitationRecords() {
    try {
        const response = await fetch(`${API_BASE}/invitation/records`, {
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
        invitationRecords = data.records || [];
        const totalInvited = data.total_invited || 0;
        
        displayInvitationRecords(invitationRecords);
        updateInvitationProgress(totalInvited);
        
    } catch (error) {
        console.error('Error fetching invitation records:', error);
        displayInvitationRecordsError();
    }
}

/**
 * 获取奖励券明细
 * MAY NEED REVIEW: 需要根据实际API设计调整
 * 假设API: GET /api/user/reward-coupons
 */
async function fetchRewardCoupons() {
    try {
        // Mock data for now - replace with actual API call
        const mockData = {
            coupons: [
                {
                    id: 1,
                    name: "邀请奖励券",
                    value: 20,
                    type: "fixed",
                    description: "无门槛20元优惠券",
                    issued_date: "2025-05-20T10:30:00Z",
                    expiry_date: "2025-05-27T23:59:59Z",
                    status: "available"
                }
            ]
        };
        
        rewardCoupons = mockData.coupons || [];
        displayRewardCoupons(rewardCoupons);
        
    } catch (error) {
        console.error('Error fetching reward coupons:', error);
        displayRewardCouponsError();
    }
}

/**
 * 显示邀请码
 * @param {string} code - 邀请码
 */
function displayInvitationCode(code) {
    const codeElement = document.getElementById('invitation-code');
    const copyBtn = document.getElementById('copy-code-btn');
    
    if (!code) {
        codeElement.innerHTML = '<div class="text-muted">邀请码获取失败</div>';
        return;
    }
    
    codeElement.innerHTML = `<span class="code-text">${code}</span>`;
    copyBtn.style.display = 'inline-block';
}

/**
 * 显示邀请码获取错误
 */
function displayInvitationCodeError() {
    const codeElement = document.getElementById('invitation-code');
    codeElement.innerHTML = `
        <div class="text-danger">
            <i class="bi bi-exclamation-triangle me-1"></i>
            获取邀请码失败，请刷新重试
        </div>
    `;
}

/**
 * 更新邀请进度
 * @param {number} totalInvited - 已邀请总数
 */
function updateInvitationProgress(totalInvited = 0) {
    const totalElement = document.getElementById('total-invited');
    const remainingElement = document.getElementById('remaining-invites');
    const progressBar = document.getElementById('progress-bar');
    
    // 每2人为一个奖励周期
    const currentCycle = totalInvited % 2;
    const remaining = 2 - currentCycle;
    const progressPercent = (currentCycle / 2) * 100;
    
    totalElement.textContent = totalInvited.toString();
    remainingElement.textContent = remaining.toString();
    
    progressBar.style.width = `${progressPercent}%`;
    progressBar.setAttribute('aria-valuenow', progressPercent.toString());
    
    // 如果已达成奖励条件，显示庆祝效果
    if (currentCycle === 0 && totalInvited > 0) {
        showRewardAchievement();
    }
}

/**
 * 显示邀请记录
 * @param {Array} records - 邀请记录数组
 */
function displayInvitationRecords(records = []) {
    const container = document.getElementById('invitation-records');
    const countBadge = document.getElementById('records-count');
    
    countBadge.textContent = `${records.length} 条记录`;
    
    if (records.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
                <div class="mt-2 text-muted">暂无邀请记录</div>
                <small class="text-muted">快去邀请好友下单吧！</small>
            </div>
        `;
        return;
    }
    
    const recordsHtml = records.map(record => `
        <div class="invitation-record-item">
            <div class="d-flex justify-content-between align-items-center">
                <div class="record-user">
                    <div class="user-name">
                        <i class="bi bi-person-circle me-1"></i>
                        ${escapeHtml(record.username)}
                    </div>
                    <small class="text-muted">用户ID: ${record.user_id}</small>
                </div>
                <div class="record-details text-end">
                    <div class="order-amount text-success fw-bold">¥${record.amount.toFixed(2)}</div>
                    <small class="text-muted">${formatDateTime(record.order_time)}</small>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = recordsHtml;
}

/**
 * 显示邀请记录错误
 */
function displayInvitationRecordsError() {
    const container = document.getElementById('invitation-records');
    container.innerHTML = `
        <div class="text-center py-4 text-danger">
            <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
            <div class="mt-2">加载邀请记录失败</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="fetchInvitationRecords()">
                重新加载
            </button>
        </div>
    `;
}

/**
 * 显示奖励券明细
 * @param {Array} coupons - 奖励券数组
 */
function displayRewardCoupons(coupons = []) {
    const container = document.getElementById('reward-coupons');
    const countBadge = document.getElementById('rewards-count');
    
    countBadge.textContent = `${coupons.length} 张奖励券`;
    
    if (coupons.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-gift text-muted" style="font-size: 3rem;"></i>
                <div class="mt-2 text-muted">暂无奖励券</div>
                <small class="text-muted">邀请2位好友即可获得首张奖励券</small>
            </div>
        `;
        return;
    }
    
    const couponsHtml = coupons.map(coupon => `
        <div class="reward-coupon-item">
            <div class="d-flex justify-content-between align-items-center">
                <div class="coupon-info">
                    <div class="coupon-name fw-bold">${escapeHtml(coupon.name)}</div>
                    <div class="coupon-description text-muted">${escapeHtml(coupon.description)}</div>
                    <small class="text-muted">发放时间：${formatDateTime(coupon.issued_date)}</small>
                </div>
                <div class="coupon-value">
                    <div class="value-display">¥${coupon.value}</div>
                    <div class="status-badge ${getStatusClass(coupon.status)}">
                        ${getStatusText(coupon.status)}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = couponsHtml;
}

/**
 * 显示奖励券错误
 */
function displayRewardCouponsError() {
    const container = document.getElementById('reward-coupons');
    container.innerHTML = `
        <div class="text-center py-4 text-danger">
            <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
            <div class="mt-2">加载奖励券失败</div>
            <button class="btn btn-outline-primary btn-sm mt-2" onclick="fetchRewardCoupons()">
                重新加载
            </button>
        </div>
    `;
}

/**
 * 绑定事件处理
 */
function bindEvents() {
    // 复制邀请码按钮
    const copyBtn = document.getElementById('copy-code-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', handleCopyInvitationCode);
    }
}

/**
 * 处理复制邀请码
 */
async function handleCopyInvitationCode() {
    if (!invitationCode) {
        showError('邀请码不可用');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(invitationCode);
        showCopySuccessToast();
    } catch (error) {
        console.error('Failed to copy invitation code:', error);
        // 降级方案：使用传统的复制方法
        fallbackCopyToClipboard(invitationCode);
    }
}

/**
 * 降级复制方法（兼容性处理）
 * @param {string} text - 要复制的文本
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccessToast();
    } catch (error) {
        console.error('Fallback copy failed:', error);
        showError('复制失败，请手动复制邀请码');
    } finally {
        document.body.removeChild(textArea);
    }
}

/**
 * 显示复制成功提示
 */
function showCopySuccessToast() {
    const toast = new bootstrap.Toast(document.getElementById('copy-toast'));
    toast.show();
}

/**
 * 显示奖励达成庆祝效果
 */
function showRewardAchievement() {
    // MAY NEED REVIEW: 可以添加更丰富的动画效果
    console.log('Reward achievement unlocked!');
}

/**
 * 显示错误信息
 * @param {string} message - 错误消息
 */
function showError(message) {
    // 创建临时错误提示
    const errorToast = document.createElement('div');
    errorToast.className = 'toast';
    errorToast.innerHTML = `
        <div class="toast-header">
            <i class="bi bi-exclamation-triangle text-danger me-2"></i>
            <strong class="me-auto">错误</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${escapeHtml(message)}</div>
    `;
    
    document.querySelector('.toast-container').appendChild(errorToast);
    const toast = new bootstrap.Toast(errorToast);
    toast.show();
    
    // 自动清理
    errorToast.addEventListener('hidden.bs.toast', () => {
        errorToast.remove();
    });
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
 * 获取优惠券状态对应的CSS类
 * @param {string} status - 优惠券状态
 * @returns {string} CSS类名
 */
function getStatusClass(status) {
    const statusClasses = {
        'available': 'badge bg-success',
        'used': 'badge bg-secondary',
        'expired': 'badge bg-danger'
    };
    return statusClasses[status] || 'badge bg-secondary';
}

/**
 * 获取优惠券状态文本
 * @param {string} status - 优惠券状态
 * @returns {string} 状态文本
 */
function getStatusText(status) {
    const statusTexts = {
        'available': '可用',
        'used': '已使用',
        'expired': '已过期'
    };
    return statusTexts[status] || '未知';
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