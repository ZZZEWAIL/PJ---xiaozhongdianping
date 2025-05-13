/**
 * Voucher Page JavaScript
 * 
 * This file handles fetching and displaying order details and voucher code.
 */

// API 基础URL
const API_BASE = "http://127.0.0.1:8000/api";

// 从 URL 获取 order_id
const urlParams = new URLSearchParams(window.location.search);
const orderId = urlParams.get('order_id');

// 存储订单数据
let orderData = null;

// 券码显示配置
const VOUCHER_CODE_CONFIG = {
    maxLength: 16, // 最大显示长度
    ellipsis: '...' // 省略号
};

// QR码配置
const QR_CODE_CONFIG = {
    width: 160,
    height: 160,
    colorDark: "#000000",
    colorLight: "#ffffff",
    correctLevel: 2, // QRCode.CorrectLevel.M，中等错误校正级别
    margin: 2
};

/**
 * 页面初始化
 */
function initPage() {
    // 检查是否有 order_id
    if (!orderId) {
        showError('未找到订单 ID');
        return;
    }

    // 设置复制券码按钮事件
    document.getElementById('copy-code').addEventListener('click', copyVoucherCode);

    // 获取订单详情
    fetchOrderDetail();
}

/**
 * 获取订单详情
 */
async function fetchOrderDetail() {
    try {
        // 显示加载状态
        document.getElementById('voucher-loading').style.display = 'block';
        document.getElementById('voucher-container').style.display = 'none';
        document.getElementById('error-container').style.display = 'none';

        const response = await fetch(
            `${API_BASE}/orders/${orderId}`, {}
        );

        if (!response.ok) {
            if (response.status === 401) {
                // 处理授权错误
                document.getElementById('voucher-loading').style.display = 'none';
                document.getElementById('login-required').style.display = 'block';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        orderData = data;

        console.log(orderData);

        // 显示订单详情
        displayOrderDetail(data);

        // 隐藏加载状态
        document.getElementById('voucher-loading').style.display = 'none';
        document.getElementById('voucher-container').style.display = 'block';
    } catch (error) {
        console.error('获取订单详情失败:', error);
        showError('无法加载订单信息，请稍后重试');
    }
}

/**
 * 显示订单详情
 * @param {Object} data - 订单详情数据
 */
function displayOrderDetail(data) {
    // 设置页面标题
    document.title = `券码详情 - ${data.package_title} - 小众点评`;

    // 设置套餐标题
    document.getElementById('package-title').textContent = data.package_title;

    // 设置订单时间
    const orderDate = new Date(data.created_at);
    document.getElementById('order-time').textContent = formatDate(orderDate);

    // 设置商店名称
    document.getElementById('shop-name').textContent = data.shop_name;

    // 设置券码
    const formattedCode = formatVoucherCode(data.voucher_code);
    document.getElementById('voucher-code').textContent = formattedCode;
    // 存储完整券码用于复制
    document.getElementById('voucher-code').dataset.fullCode = data.voucher_code;

    // 生成二维码
    generateQRCode(data.voucher_code);
}

/**
 * 生成二维码
 * @param {string} code - 要编码的券码
 */
function generateQRCode(code) {
    if (!code) return;

    // 清空已有的 QR 码（如果存在）
    const qrcodeElement = document.getElementById('qrcode');
    qrcodeElement.innerHTML = '';

    try {
        // 创建 QR 码
        new QRCode(qrcodeElement, {
            text: code,
            width: QR_CODE_CONFIG.width,
            height: QR_CODE_CONFIG.height,
            colorDark: QR_CODE_CONFIG.colorDark,
            colorLight: QR_CODE_CONFIG.colorLight,
            correctLevel: QR_CODE_CONFIG.correctLevel,
            margin: QR_CODE_CONFIG.margin
        });
    } catch (error) {
        console.error('生成 QR 码失败:', error);
        // 在生成 QR 码失败时优雅地处理错误
        qrcodeElement.innerHTML = `<div class="text-center text-danger">
            <i class="bi bi-exclamation-triangle"></i>
            <p class="small mt-1">QR码生成失败</p>
        </div>`;
    }
}

/**
 * 解析并显示套餐内容
 * @param {string} contentsString - 套餐内容字符串
 */
function displayPackageContents(contentsString) {
    const contentsContainer = document.getElementById('package-contents');
    contentsContainer.innerHTML = '';

    // 如果没有内容，显示提示信息
    if (!contentsString || contentsString.trim() === '') {
        contentsContainer.innerHTML = '<li class="list-group-item">暂无套餐内容信息</li>';
        return;
    }

    // 尝试将内容拆分为项目列表
    // 假设内容是用换行符或分号分隔的
    let contentItems = [];
    if (contentsString.includes('\n')) {
        contentItems = contentsString.split('\n');
    } else if (contentsString.includes(';')) {
        contentItems = contentsString.split(';');
    } else {
        // 如果没有明确的分隔符，就将整个字符串作为一个项目
        contentItems = [contentsString];
    }

    // 添加每个内容项
    contentItems.forEach(item => {
        if (item.trim() !== '') {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            listItem.textContent = item.trim();
            contentsContainer.appendChild(listItem);
        }
    });
}

/**
 * 格式化券码显示
 * @param {string} code - 原始券码
 * @returns {string} 格式化后的券码
 */
function formatVoucherCode(code) {
    if (!code) return '';

    if (code.length <= VOUCHER_CODE_CONFIG.maxLength) {
        return code;
    }

    // 在中间添加省略号
    const halfLength = Math.floor((VOUCHER_CODE_CONFIG.maxLength - VOUCHER_CODE_CONFIG.ellipsis.length) / 2);
    return code.slice(0, halfLength) + VOUCHER_CODE_CONFIG.ellipsis + code.slice(-halfLength);
}

/**
 * 复制券码到剪贴板
 */
function copyVoucherCode() {
    const voucherCodeElement = document.getElementById('voucher-code');
    const fullCode = voucherCodeElement.dataset.fullCode || voucherCodeElement.textContent;

    if (!fullCode) return;

    navigator.clipboard.writeText(fullCode)
        .then(() => {
            // 显示复制成功提示
            const toastElement = document.getElementById('copy-toast');
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
        })
        .catch(err => {
            console.error('复制券码失败:', err);
            alert('复制券码失败，请手动复制');
        });
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showError(message) {
    document.getElementById('voucher-loading').style.display = 'none';

    const errorContainer = document.getElementById('error-container');
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
}

/**
 * 格式化日期为友好显示格式
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date) {
    // 检查是否为有效日期
    if (!(date instanceof Date) || isNaN(date)) {
        return '未知日期';
    }

    // 格式化为完整日期时间
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 页面加载时初始化
window.onload = initPage;