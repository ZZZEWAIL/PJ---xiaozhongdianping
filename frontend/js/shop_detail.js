document.addEventListener('DOMContentLoaded', async function () {
    const urlParams = new URLSearchParams(window.location.search);
    const shopId = urlParams.get('id');
    const errorMessage = document.createElement('p');
    errorMessage.id = 'error-message';
    errorMessage.classList.add('error');
    const contentDiv = document.querySelector('.page-content');
    contentDiv.appendChild(errorMessage);

    if (!shopId) {
        console.error('未提供商家 ID');
        errorMessage.textContent = '未提供商家 ID，请返回重新选择';
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/shops/${shopId}`, {
            method: 'GET',
            credentials: 'include',
        });

        if (response.ok) {
            const shop = await response.json();
            document.getElementById('shop-name').textContent = shop.name;
            document.getElementById('shop-category').textContent = shop.category;
            document.getElementById('shop-rating').textContent = shop.rating;
            document.getElementById('shop-avg-cost').textContent = shop.avg_cost;
            document.getElementById('shop-address').textContent = shop.address;
            document.getElementById('shop-phone').textContent = shop.phone;
            document.getElementById('shop-business-hours').textContent = shop.business_hours;

            const shopImagesDiv = document.getElementById('shop-images');
            shop.image_urls.forEach((imageUrl) => {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = `商家 ${shop.name} 的图片`;
                shopImagesDiv.appendChild(img);
            });
        } else {
            console.error('获取商家详情失败');
            errorMessage.textContent = '获取商家详情失败，请稍后重试';
        }
    } catch (error) {
        console.error('Error:', error);
        errorMessage.textContent = '网络错误，请稍后重试';
    }
});