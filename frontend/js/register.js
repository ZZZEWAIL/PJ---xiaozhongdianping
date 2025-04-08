document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('register-form');
    const errorMessage = document.getElementById('error-message');
    const captchaImage = document.getElementById('captcha-image');
    const refreshCaptchaButton = document.getElementById('refresh-captcha');
    const passwordInput = document.getElementById('password');
    const passwordStrength = document.getElementById('password-strength');

    if (!form || !captchaImage || !refreshCaptchaButton || !passwordInput || !passwordStrength) {
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
            captchaImage.src = '';
        }
    }

    // 初次加载验证码
    loadCaptcha();

    // 刷新验证码
    refreshCaptchaButton.addEventListener('click', loadCaptcha);

    // 实时检测密码强度
    passwordInput.addEventListener('input', function () {
        const password = passwordInput.value;
        let strengthText = '';
        let strengthClass = '';

        // 密码强度标准
        if (password.length < 6 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
            strengthText = '弱';
            strengthClass = 'weak';
        } else if (password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password)) {
            if (password.length >= 10 && /[!@#$%^&*]/.test(password)) {
                strengthText = '强';
                strengthClass = 'strong';
            } else {
                strengthText = '中';
                strengthClass = 'medium';
            }
        } else {
            strengthText = '弱';
            strengthClass = 'weak';
        }

        // 更新密码强度提示
        passwordStrength.textContent = `密码强度：${strengthText}`;
        passwordStrength.className = `password-strength fadeIn third ${strengthClass}`;
    });

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
                credentials: 'include', // 确保请求携带 Cookie
            });

            if (!response.ok) {
                const errorData = await response.json();
                errorMessage.textContent = errorData.detail || '注册失败';
                loadCaptcha(); // 刷新验证码
                return;
            }

            // 注册成功
            errorMessage.textContent = '注册成功！';
            setTimeout(() => {
                window.location.href = 'login.html'; // 跳转到登录页面
            }, 1000);
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = '网络错误，请稍后重试';
            loadCaptcha(); // 刷新验证码
        }
    });
});