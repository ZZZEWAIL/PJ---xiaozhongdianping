/**
 * New User Coupon JS
 * 
 * This script handles:
 * 1. Fetching available new user coupons
 * 2. Displaying them with appropriate states
 * 3. Handling the coupon claim process
 */

// DOM Elements
const loadingContainer = document.getElementById('loading-container');
const errorContainer = document.getElementById('error-container');
const alreadyClaimedContainer = document.getElementById('already-claimed-container');
const couponsContainer = document.getElementById('coupons-container');
const couponList = document.getElementById('coupon-list');
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');
const successMessage = document.getElementById('success-message');

// Bootstrap Modal
let successModal;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize success modal
    successModal = new bootstrap.Modal(document.getElementById('successModal'));
    
    // Add event listener for retry button
    retryBtn.addEventListener('click', fetchNewUserCoupons);
    
    // Fetch coupons on page load
    fetchNewUserCoupons();
});

/**
 * Fetch available new user coupons from the API
 */
async function fetchNewUserCoupons() {
    // Show loading
    showLoading();
    
    try {
        const response = await fetch('/api/coupons/new_user/available', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Check if user is not eligible (already claimed)
            if (response.status === 400 && data.detail.includes('已领取')) {
                showAlreadyClaimed();
                return;
            }
            
            throw new Error(data.detail || '获取优惠券失败');
        }
        
        // Check if user is eligible
        if (!data.eligible) {
            showAlreadyClaimed();
            return;
        }
        
        // Render coupons
        renderCoupons(data.coupons);
        
    } catch (error) {
        console.error('Error fetching new user coupons:', error);
        showError(error.message);
    }
}

/**
 * Claim a selected coupon
 * @param {string} couponType - The type of coupon to claim (kfc, milk_tea, discount)
 * @param {string} couponName - The name of the coupon for display in success message
 */
async function claimCoupon(couponType, couponName) {
    try {
        // Disable all buttons to prevent multiple claims
        document.querySelectorAll('.claim-btn').forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 领取中...';
        });
        
        const response = await fetch(`/api/coupons/new_user/claim/${couponType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '领取优惠券失败');
        }
        
        // Show success message
        successMessage.textContent = `恭喜您！成功领取了${couponName}`;
        successModal.show();
        
    } catch (error) {
        console.error('Error claiming coupon:', error);
        showError(error.message);
        
        // Re-enable buttons
        document.querySelectorAll('.claim-btn').forEach(btn => {
            btn.disabled = false;
            btn.innerHTML = '立即领取';
        });
    }
}

/**
 * Render the coupons in the UI
 * @param {Array} coupons - List of coupon objects
 */
function renderCoupons(coupons) {
    // Clear previous content
    couponList.innerHTML = '';
    
    if (!coupons || coupons.length === 0) {
        showError('暂无可领取的优惠券');
        return;
    }
    
    // Generate HTML for each coupon
    coupons.forEach(coupon => {
        const couponCard = createCouponCard(coupon);
        couponList.appendChild(couponCard);
    });
    
    // Show coupons container
    hideAll();
    couponsContainer.classList.remove('d-none');
}

/**
 * Create a coupon card element
 * @param {Object} coupon - Coupon object
 * @returns {HTMLElement} - The coupon card element
 */
function createCouponCard(coupon) {
    const col = document.createElement('div');
    col.className = 'col-md-4';
    
    // Set coupon color based on type
    let cardColor, borderColor, btnClass;
    switch (coupon.type) {
        case 'kfc':
            cardColor = 'bg-danger bg-opacity-10';
            borderColor = 'border-danger';
            btnClass = 'btn-danger';
            break;
        case 'milk_tea':
            cardColor = 'bg-info bg-opacity-10';
            borderColor = 'border-info';
            btnClass = 'btn-info';
            break;
        case 'discount':
            cardColor = 'bg-warning bg-opacity-10';
            borderColor = 'border-warning';
            btnClass = 'btn-warning';
            break;
        default:
            cardColor = 'bg-primary bg-opacity-10';
            borderColor = 'border-primary';
            btnClass = 'btn-primary';
    }
    
    // Format discount value for display
    let discountDisplay;
    if (coupon.discount_type === 'discount') {
        discountDisplay = `${(coupon.discount_value * 10).toFixed(0)}折`;
    } else if (coupon.min_spend > 0) {
        discountDisplay = `满${coupon.min_spend}减${coupon.discount_value}元`;
    } else {
        discountDisplay = `立减${coupon.discount_value}元`;
    }
    
    // Create HTML
    const isDisabled = coupon.remaining === '已发完';
    
    col.innerHTML = `
        <div class="card h-100 shadow-sm ${cardColor} border ${borderColor}">
            <div class="card-body">
                <h5 class="card-title">${coupon.name}</h5>
                <div class="discount-value mb-3">${discountDisplay}</div>
                <p class="card-text small text-muted">${coupon.description || ''}</p>
                <div class="d-flex justify-content-between align-items-center mt-3">
                    <span class="badge bg-secondary">${coupon.remaining}</span>
                    <span class="badge bg-secondary">${coupon.valid_days}天有效</span>
                </div>
            </div>
            <div class="card-footer bg-transparent border-0 d-grid">
                <button class="btn ${btnClass} claim-btn" 
                    onclick="claimCoupon('${coupon.type}', '${coupon.name}')"
                    ${isDisabled ? 'disabled' : ''}>
                    ${isDisabled ? '已抢光' : '立即领取'}
                </button>
            </div>
        </div>
    `;
    
    return col;
}

// UI State Management Functions
function hideAll() {
    loadingContainer.classList.add('d-none');
    errorContainer.classList.add('d-none');
    alreadyClaimedContainer.classList.add('d-none');
    couponsContainer.classList.add('d-none');
}

function showLoading() {
    hideAll();
    loadingContainer.classList.remove('d-none');
}

function showError(message) {
    hideAll();
    errorMessage.textContent = message || '获取优惠券失败，请稍后再试';
    errorContainer.classList.remove('d-none');
}

function showAlreadyClaimed() {
    hideAll();
    alreadyClaimedContainer.classList.remove('d-none');
} 