document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('register-form');
    const errorMessage = document.getElementById('error-message');
    const captchaImage = document.getElementById('captcha-image');
    const refreshCaptchaButton = document.getElementById('refresh-captcha');

    if (!form || !captchaImage || !refreshCaptchaButton) {
        console.error('Form or captcha elements not found');
        return;
    }

    // 加载验证码
    async function loadCaptcha() {
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/captcha');
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Failed to load captcha: ${response.status} - ${errorData.detail || 'Unknown error'}`);
            }
            const data = await response.json();
            if (data.captcha_image) {
                captchaImage.src = data.captcha_image;
            } else {
                throw new Error('No captcha image in response');
            }
        } catch (error) {
            console.error('Error loading captcha:', error);
            errorMessage.textContent = `加载验证码失败: ${error.message}`;
            captchaImage.src = ''; // 清空无效图片
        }
    }

    // 初次加载验证码
    loadCaptcha();

    // 刷新验证码
    refreshCaptchaButton.addEventListener('click', loadCaptcha);

    // 表单提交
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const captcha = document.getElementById('captcha').value;

        try {
            const response = await fetch('http://127.0.0.1:8000/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password, captcha }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                errorMessage.textContent = errorData.detail || '注册失败';
                loadCaptcha(); // 刷新验证码
                return;
            }

            const data = await response.json();
            errorMessage.textContent = '注册成功！';
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1000);
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = '网络错误，请稍后重试';
            loadCaptcha(); // 刷新验证码
        }
    });
});