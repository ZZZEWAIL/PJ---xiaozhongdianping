// 从 URL 获取 shop_id
const urlParams = new URLSearchParams(window.location.search);
const shopId = urlParams.get('shop_id');
const API_BASE = "http://127.0.0.1:8000/api/shops";

// 分页参数
let currentImagePage = 1;
const imagePageSize = 1; // 每页显示 1 张图片

// 获取并展示商家详情
async function fetchShopDetail() {
    if (!shopId) {
        alert('未找到商家 ID');
        window.location.href = 'search.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/${shopId}?image_page=${currentImagePage}&image_page_size=${imagePageSize}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displayShopDetail(data);

        // 获取套餐数据
        fetchPackages();
    } catch (err) {
        console.error('Fetch shop detail error:', err);
        alert('无法加载商家详情，请稍后重试');
    }
}

// 展示商家详情和图片
function displayShopDetail(data) {
    const shopDetailContainer = document.getElementById('shop-detail');
    const imageContainer = document.getElementById('image-container');
    const imagePageInfo = document.getElementById('image-page-info');
    const prevButton = document.getElementById('prev-image');
    const nextButton = document.getElementById('next-image');

    // 展示商家信息
    const shop = data.shop;
    shopDetailContainer.innerHTML = `
        <h3>${shop.name}</h3>
        <p><strong>类别:</strong> ${shop.category}</p>
        <p><strong>评分:</strong> ${shop.rating}</p>
        <p><strong>价格范围:</strong> ${shop.price_range}</p>
        <p><strong>人均消费:</strong> ￥${shop.avg_cost}</p>
        <p><strong>地址:</strong> ${shop.address}</p>
        <p><strong>电话:</strong> ${shop.phone}</p>
        <p><strong>营业时间:</strong> ${shop.business_hours}</p>
        ${shop.image_url ? `<img src="${shop.image_url}" alt="${shop.name}" style="max-width: 100%; border-radius: 8px;">` : ''}
    `;

    // 展示图片
    const images = data.images;
    if (images.data.length > 0) {
        imageContainer.innerHTML = `<img src="${images.data[0].image_url}" alt="Shop Image">`;
    } else {
        imageContainer.innerHTML = '<p>暂无图片</p>';
    }

    // 更新分页信息
    const totalPages = Math.ceil(images.total / images.page_size);
    imagePageInfo.textContent = `第 ${images.page} 页 / 共 ${totalPages} 页`;

    // 控制分页按钮
    prevButton.disabled = images.page <= 1;
    nextButton.disabled = images.page >= totalPages;

    // 更新全局分页参数
    currentImagePage = images.page;
}

/**
 * 获取店铺的团购套餐列表
 */
async function fetchPackages() {
    try {
        const packagesContainer = document.getElementById('packages-container');
        
        const response = await fetch(`${API_BASE}/${shopId}/packages`);
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
 * @param {Array} packages 套餐列表数据
 */
function displayPackages(packages) {
    const packagesContainer = document.getElementById('packages-container');
    
    if (!packages || packages.length === 0) {
        packagesContainer.innerHTML = `
            <div class="col-12 text-center">
                <p>暂无套餐</p>
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
                        <h5 class="card-title">${pkg.title}</h5>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="price">¥${pkg.price.toFixed(2)}</span>
                            <span class="sales-badge">已售${pkg.sales}份</span>
                        </div>
                        <p class="card-text content-preview">${pkg.contents}</p>
                    </div>
                    <div class="card-footer bg-transparent text-center">
                        <button class="btn btn-outline-primary view-detail-btn">查看详情</button>
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
            window.location.href = `package_detail.html?package_id=${packageId}`;
        });
    });
}

// 上一页
document.getElementById('prev-image').addEventListener('click', () => {
    if (currentImagePage > 1) {
        currentImagePage--;
        fetchShopDetail();
    }
});

// 下一页
document.getElementById('next-image').addEventListener('click', () => {
    currentImagePage++;
    fetchShopDetail();
});

// 初始加载
window.onload = fetchShopDetail;