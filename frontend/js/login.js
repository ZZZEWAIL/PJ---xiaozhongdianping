document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok) {
        console.log('Login successful', data);
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('token_type', data.token_type);
        window.location.href = 'index.html';
    } else {
        console.error('Login failed', data);
        alert('Invalid username or password');
    }
});