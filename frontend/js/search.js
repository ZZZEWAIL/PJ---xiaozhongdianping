// frontend/js/search.js

const API_BASE = "http://127.0.0.1:8000/api/shops/search";
const HISTORY_API = "http://127.0.0.1:8000/api/shops/search/history";
let lastFetchedData = [];

function init() {
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', () => handleSearch(1)); // 明确传入 page 参数
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
            applyFilters(1); // 明确传入 page 参数
        });
        console.log('Filters form listener added');
    } else {
        console.error('Filters form not found');
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => applySortAndShow(1)); // 明确传入 page 参数
        console.log('Sort select listener added');
    } else {
        console.error('Sort select not found');
    }

    renderSearchHistory();
}

document.addEventListener('DOMContentLoaded', init);

function handleSearch(page = 1) {
    console.log('handleSearch triggered');
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }
    console.log('Search triggered with keyword:', keyword);

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    const url = `${API_BASE}?keyword=${encodeURIComponent(keyword)}&page=${page}&page_size=10`;
    console.log('Search URL:', url);
    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(response => {
            lastFetchedData = response.data;
            resultsContainer.classList.remove('loading');
            showResults(response);
        })
        .catch(err => {
            console.error('Fetch error:', err);
            resultsContainer.classList.remove('loading');
            alert('搜索失败，请稍后重试');
        });
}

function applyFilters(page = 1) {
    console.log('applyFilters triggered');
    const formData = new FormData(document.getElementById('filters'));
    const params = new URLSearchParams();
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }
    params.set('keyword', encodeURIComponent(keyword));
    params.set('page', page);
    params.set('page_size', '10');

    for (const [key, value] of formData) {
        if (key === 'ratings') {
            params.append('ratings', value);
        } else if (key === 'avg_cost') {
            const [min, max] = value.split('-');
            params.set('avg_cost_min', min);
            params.set('avg_cost_max', max);
        }
    }

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    const url = `${API_BASE}?${params.toString()}`;
    console.log('Filter URL:', url);
    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(response => {
            lastFetchedData = response.data;
            resultsContainer.classList.remove('loading');
            showResults(response);
        })
        .catch(err => {
            console.error('Filter fetch error:', err);
            resultsContainer.classList.remove('loading');
            alert('筛选失败，请稍后重试');
        });
}

function applySortAndShow(page = 1) {
    console.log('applySortAndShow triggered');
    const sortValue = document.getElementById('sortSelect').value;
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键字');
        return;
    }

    const params = new URLSearchParams();
    params.set('keyword', encodeURIComponent(keyword));
    params.set('page', page);
    params.set('page_size', '10');

    if (sortValue === 'rating_desc') {
        params.set('sort_by', 'rating');
        params.set('sort_order', 'desc');
    } else if (sortValue === 'avg_desc') {
        params.set('sort_by', 'avg_cost');
        params.set('sort_order', 'desc');
    } else {
        params.set('sort_by', 'default');
        params.set('sort_order', 'desc');
    }

    const url = `${API_BASE}?${params.toString()}`;
    console.log('Sort URL:', url);

    const resultsContainer = document.getElementById('results');
    resultsContainer.classList.add('loading');

    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(response => {
            lastFetchedData = response.data;
            resultsContainer.classList.remove('loading');
            showResults(response);
        })
        .catch(err => {
            console.error('Sort fetch error:', err);
            resultsContainer.classList.remove('loading');
            alert('排序失败，请稍后重试');
        });
}

function renderSearchHistory() {
    console.log('renderSearchHistory triggered');
    fetch(HISTORY_API)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        })
        .then(history => {
            const listEl = document.getElementById('historyList');
            listEl.innerHTML = '';
            history.forEach(keyword => {
                const li = document.createElement('li');
                li.textContent = keyword;
                li.onclick = () => {
                    document.getElementById('searchInput').value = keyword;
                    handleSearch(1); // 明确传入 page 参数
                };
                listEl.appendChild(li);
            });
        })
        .catch(err => {
            console.error('History fetch error:', err);
        });
}

function clearSearchHistory() {
    console.log('clearSearchHistory triggered');
    fetch(HISTORY_API, { method: 'DELETE' })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            alert('搜索历史已清除');
            renderSearchHistory();
        })
        .catch(err => {
            console.error('Clear history error:', err);
            alert('清除历史失败，请稍后重试');
        });
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
    data.forEach(shop => {
        const card = document.createElement('div');
        card.className = 'result-item'; // 改为垂直排列的类名
        card.innerHTML = `
            <div class="result-card">
                <h5>${shop.name}</h5>
                <p>类别: ${shop.category}</p>
                <p>评分: ${shop.rating}</p>
                <p>人均消费: ￥${shop.avg_cost}</p>
                <p>地址: ${shop.address}</p>
            </div>
        `;
        resultsContainer.appendChild(card);
    });

    // 显示分页导航
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

        // 上一页
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.textContent = '上一页';
        prevLink.onclick = (e) => {
            e.preventDefault();
            if (page > 1) {
                handleSearch(page - 1); // 正确传递页码
            }
        };
        prevLi.appendChild(prevLink);
        ul.appendChild(prevLi);

        // 页码
        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === page ? 'active' : ''}`;
            const link = document.createElement('a');
            link.className = 'page-link';
            link.href = '#';
            link.textContent = i;
            link.onclick = (e) => {
                e.preventDefault();
                handleSearch(i); // 正确传递页码
            };
            li.appendChild(link);
            ul.appendChild(li);
        }

        // 下一页
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.textContent = '下一页';
        nextLink.onclick = (e) => {
            e.preventDefault();
            if (page < totalPages) {
                handleSearch(page + 1); // 正确传递页码
            }
        };
        nextLi.appendChild(nextLink);
        ul.appendChild(nextLi);

        nav.appendChild(ul);
        paginationContainer.appendChild(nav);
    }
}