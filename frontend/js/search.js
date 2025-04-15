const API_BASE = "http://127.0.0.1:8000/api/shops/search";
const HISTORY_API = "http://127.0.0.1:8000/api/shops/search/history";
let lastFetchedData = [];
let currentFilters = {}; // 新增：存储当前的筛选条件

function init() {
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', () => handleSearch(1));
        console.log('Search button listener added');
    } else {
        console.error('Search button not found');
    }

    const clearHistoryButton = document.getElementById('clearHistoryButton');
    if (clearHistoryButton) {
        clearHistoryButton.addEventListener('click', clearSearchHistory);
        console.log('Clear history button listener added');
    } else {
        console.error('Clear history button not found');
    }

    const filtersForm = document.getElementById('filters');
    if (filtersForm) {
        filtersForm.addEventListener('submit', function (e) {
            e.preventDefault();
            applyFilters(1);
        });
        console.log('Filters form listener added');
    } else {
        console.error('Filters form not found');
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => applySortAndShow(1));
        console.log('Sort select listener added');
    } else {
        console.error('Sort select not found');
    }

    renderSearchHistory();
}

document.addEventListener('DOMContentLoaded', init);

async function handleSearch(page = 1) {
    console.log('handleSearch triggered');
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }
    console.log('Search triggered with keyword:', keyword);
    console.log('Raw keyword (hex):', Array.from(keyword).map(c => c.charCodeAt(0).toString(16)).join(' '));

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    const params = new URLSearchParams();
    params.set('keyword', keyword);
    params.set('page', page);
    params.set('page_size', '10');

    // 应用当前的筛选条件
    if (currentFilters.ratings) {
        params.append('ratings', currentFilters.ratings);
    }
    if (currentFilters.avg_cost_min) {
        params.set('avg_cost_min', currentFilters.avg_cost_min);
    }
    if (currentFilters.avg_cost_max) {
        params.set('avg_cost_max', currentFilters.avg_cost_max);
    }
    if (currentFilters.is_open) {
        params.set('is_open', 'true'); // 新增：营业中筛选
    }

    const sortValue = document.getElementById('sortSelect').value;
    if (sortValue === 'rating_desc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'rating_asc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'asc');
    } else if (sortValue === 'avg_desc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'avg_asc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'asc');
    } else {
        params.set('sort_by', 'default');
        params.set('sort_order', 'desc');
    }

    const url = `${API_BASE}?${params.toString()}`;
    console.log('Search URL:', url);

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const response = await res.json();
        lastFetchedData = response.data;
        resultsContainer.classList.remove('loading');
        showResults(response);
        await renderSearchHistory();
    } catch (err) {
        console.error('Fetch error:', err);
        resultsContainer.classList.remove('loading');
        alert('搜索失败，请稍后重试');
    }
}

async function applyFilters(page = 1) {
    console.log('applyFilters triggered');
    lastFetchedData = [];
    const formData = new FormData(document.getElementById('filters'));
    const params = new URLSearchParams();
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }
    console.log('Filter triggered with keyword:', keyword);
    console.log('Raw keyword (hex):', Array.from(keyword).map(c => c.charCodeAt(0).toString(16)).join(' '));

    params.set('keyword', keyword);
    params.set('page', page);
    params.set('page_size', '10');

    // 重置筛选条件
    currentFilters = {};

    // 处理多个 avg_cost 筛选条件
    let avgCostRanges = formData.getAll('avg_cost'); // 获取所有 avg_cost 值
    if (avgCostRanges.length > 0) {
        let minCost = Infinity;
        let maxCost = -Infinity;
        avgCostRanges.forEach(range => {
            const [min, max] = range.split('-').map(Number);
            minCost = Math.min(minCost, min);
            maxCost = Math.max(maxCost, max);
        });
        console.log('Applying avg_cost filter: min=', minCost, 'max=', maxCost);
        params.set('avg_cost_min', minCost);
        params.set('avg_cost_max', maxCost);
        currentFilters.avg_cost_min = minCost;
        currentFilters.avg_cost_max = maxCost;
    }

    // 处理 ratings 筛选
    const ratings = formData.get('ratings');
    if (ratings) {
        console.log('Applying ratings filter:', ratings);
        params.append('ratings', ratings);
        currentFilters.ratings = ratings;
    }

    // 处理 is_open 筛选
    const isOpen = formData.get('is_open');
    if (isOpen === 'true') {
        console.log('Applying is_open filter:', isOpen);
        params.set('is_open', 'true');
        currentFilters.is_open = true;
    }

    const sortValue = document.getElementById('sortSelect').value;
    if (sortValue === 'rating_desc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'rating_asc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'asc');
    } else if (sortValue === 'avg_desc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'avg_asc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'asc');
    } else {
        params.set('sort_by', 'default');
        params.set('sort_order', 'desc');
    }

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    const url = `${API_BASE}?${params.toString()}`;
    console.log('Filter URL:', url);
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const response = await res.json();
        lastFetchedData = response.data;
        resultsContainer.classList.remove('loading');
        showResults(response);
        await renderSearchHistory();
    } catch (err) {
        console.error('Filter fetch error:', err);
        resultsContainer.classList.remove('loading');
        alert('筛选失败，请稍后重试');
    }
}

async function applySortAndShow(page = 1) {
    console.log('applySortAndShow triggered');
    lastFetchedData = [];
    const sortValue = document.getElementById('sortSelect').value;
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }
    console.log('Sort triggered with keyword:', keyword);
    console.log('Raw keyword (hex):', Array.from(keyword).map(c => c.charCodeAt(0).toString(16)).join(' '));

    const params = new URLSearchParams();
    params.set('keyword', keyword);
    params.set('page', page);
    params.set('page_size', '10');

    // 应用当前的筛选条件
    if (currentFilters.ratings) {
        params.append('ratings', currentFilters.ratings);
    }
    if (currentFilters.avg_cost_min) {
        params.set('avg_cost_min', currentFilters.avg_cost_min);
    }
    if (currentFilters.avg_cost_max) {
        params.set('avg_cost_max', currentFilters.avg_cost_max);
    }
    if (currentFilters.is_open) {
        params.set('is_open', 'true'); // 新增：营业中筛选
    }

    if (sortValue === 'rating_desc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'rating_asc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'asc');
    } else if (sortValue === 'avg_desc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'avg_asc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'asc');
    } else {
        params.set('sort_by', 'default');
        params.set('sort_order', 'desc');
    }

    const url = `${API_BASE}?${params.toString()}`;
    console.log('Sort URL:', url);

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const response = await res.json();
        lastFetchedData = response.data;
        resultsContainer.classList.remove('loading');
        showResults(response);
        await renderSearchHistory();
    } catch (err) {
        console.error('Sort fetch error:', err);
        resultsContainer.classList.remove('loading');
        alert('排序失败，请稍后重试');
    }
}

async function renderSearchHistory() {
    console.log('renderSearchHistory triggered');
    const listEl = document.getElementById('historyList');
    if (!listEl) {
        console.error('History list element not found');
        return;
    }

    listEl.innerHTML = '';
    try {
        const res = await fetch(`${API_BASE}/history`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const history = await res.json();
        console.log('Search history:', history);

        if (history.length === 0) {
            listEl.innerHTML = '<p>暂无搜索历史</p>';
            return;
        }

        history.forEach(keyword => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="history-keyword">${keyword}</span>
                <span class="delete-btn"><i class="bi bi-x-circle"></i></span>
            `;
            // 为词条内容绑定搜索事件
            const keywordSpan = li.querySelector('.history-keyword');
            keywordSpan.addEventListener('click', () => {
                console.log('Setting search input to:', keyword);
                console.log('Raw keyword (hex):', Array.from(keyword).map(c => c.charCodeAt(0).toString(16)).join(' '));
                document.getElementById('searchInput').value = keyword;
                handleSearch(1);
            });
            // 为删除按钮绑定删除事件
            const deleteBtn = li.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                deleteHistoryItem(keyword);
            });
            listEl.appendChild(li);
        });
    } catch (err) {
        console.error('History fetch error:', err);
        listEl.innerHTML = '<p>加载历史记录失败</p>';
    }
}


async function clearSearchHistory() {
    console.log('clearSearchHistory triggered');
    try {
        const res = await fetch(HISTORY_API, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        alert('搜索历史已清除');
        await renderSearchHistory();
    } catch (err) {
        console.error('Clear history error:', err);
        alert('清除历史失败，请稍后重试');
    }
}

function showResults(response) {
    console.log('showResults triggered');
    console.log('Response data:', response);
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';
    const data = response.data;
    if (!data || data.length === 0) {
        resultsContainer.innerHTML = '<p>暂无结果</p>';
        return;
    }
    console.log('Rendering shops in order:', data.map(shop => ({
        name: shop.name,
        rating: shop.rating,
        avg_cost: shop.avg_cost
    })));
    data.forEach((shop, shopIndex) => {
        const card = document.createElement('div');
        card.className = 'result-item';
        card.innerHTML = `
            <div class="result-card">
                <!-- 轮播图 -->
                <div id="carousel-${shopIndex}" class="carousel slide" data-bs-ride="carousel">
                    <div class="carousel-inner">
                        ${shop.image_urls.map((url, index) => `
                            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                                <img src="${url}" class="d-block w-100 shop-image" alt="${shop.name} - Image ${index + 1}">
                            </div>
                        `).join('')}
                    </div>
                    <!-- 轮播控件 -->
                    <button class="carousel-control-prev" type="button" data-bs-target="#carousel-${shopIndex}" data-bs-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Previous</span>
                    </button>
                    <button class="carousel-control-next" type="button" data-bs-target="#carousel-${shopIndex}" data-bs-slide="next">
                        <span class="carousel-control-next-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Next</span>
                    </button>
                </div>
                <h5>${shop.name}</h5>
                <p>类别: ${shop.category}</p>
                <p>评分: ${shop.rating}</p>
                <p>人均消费: ￥${shop.avg_cost}</p>
                <p>地址: ${shop.address}</p>
                ${shop.is_open ? '<span class="open-badge">营业中</span>' : ''}
            </div>
        `;
        card.addEventListener('click', () => {
            console.log('Navigating to shop_id:', shop.id);
            window.location.href = `shops_detail.html?shop_id=${shop.id}`;
        });
        resultsContainer.appendChild(card);
    });

    const paginationContainer = document.getElementById('pagination');
    paginationContainer.innerHTML = '';
    const total = response.total;
    const page = response.page;
    const pageSize = response.page_size;
    const totalPages = Math.ceil(total / pageSize);

    if (totalPages > 1) {
        const nav = document.createElement('nav');
        nav.setAttribute('aria-label', 'Page navigation');
        const ul = document.createElement('ul');
        ul.className = 'pagination justify-content-center';

        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.textContent = '上一页';
        prevLink.onclick = (e) => {
            e.preventDefault();
            if (page > 1) {
                handleSearch(page - 1);
            }
        };
        prevLi.appendChild(prevLink);
        ul.appendChild(prevLi);

        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === page ? 'active' : ''}`;
            const link = document.createElement('a');
            link.className = 'page-link';
            link.href = '#';
            link.textContent = i;
            link.onclick = (e) => {
                e.preventDefault();
                handleSearch(i);
            };
            li.appendChild(link);
            ul.appendChild(li);
        }

        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.textContent = '下一页';
        nextLink.onclick = (e) => {
            e.preventDefault();
            if (page < totalPages) {
                handleSearch(page + 1);
            }
        };
        nextLi.appendChild(nextLink);
        ul.appendChild(nextLi);

        nav.appendChild(ul);
        paginationContainer.appendChild(nav);
    }
}