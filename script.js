// Theme Management
function changeTheme(theme) {
    document.body.className = `theme-${theme}`;
    localStorage.setItem('selectedTheme', theme);
    showNotification('تم تغيير الثيم بنجاح', 'success');
}

// Load saved theme
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('selectedTheme') || 'black';
    document.body.className = `theme-${savedTheme}`;
});

// Form Switching
function showRegisterForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
}

function showLoginForm() {
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

// Handle Login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const role = document.querySelector('input[name="loginRole"]:checked').value;
    
    // Try backend API first
    const result = await apiLogin({ username, password, role });
    
    if (result.success) {
        showNotification('تم تسجيل الدخول بنجاح', 'success');
        setTimeout(() => {
            if (role === 'student') {
                window.location.href = 'student-dashboard.html';
            } else {
                window.location.href = 'employee-dashboard.html';
            }
        }, 1000);
    } else {
        // Fallback to localStorage if backend is offline
        const localResult = loginUser(username, password, role);
        if (localResult.success) {
            showNotification('تم تسجيل الدخول بنجاح (وضع محلي)', 'success');
            setTimeout(() => {
                if (role === 'student') {
                    window.location.href = 'student-dashboard.html';
                } else {
                    window.location.href = 'employee-dashboard.html';
                }
            }, 1000);
        } else {
            showNotification(result.message || localResult.message, 'error');
        }
    }
}

// Handle Registration
async function handleRegister(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('registerFullName').value;
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    const role = document.querySelector('input[name="registerRole"]:checked').value;
    
    // Validation
    if (password !== confirmPassword) {
        showNotification('كلمات المرور غير متطابقة', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error');
        return;
    }
    
    const userData = {
        fullName,
        username,
        email,
        password,
        role
    };
    
    // Try backend API first
    const result = await apiRegister(userData);
    
    if (result.success) {
        showNotification(result.message, 'success');
        setTimeout(() => {
            showLoginForm();
            document.getElementById('registerForm').querySelector('form').reset();
        }, 1500);
    } else {
        // Fallback to localStorage
        const localResult = registerUser(userData);
        if (localResult.success) {
            showNotification(localResult.message + ' (وضع محلي)', 'success');
            setTimeout(() => {
                showLoginForm();
                document.getElementById('registerForm').querySelector('form').reset();
            }, 1500);
        } else {
            showNotification(result.message || localResult.message, 'error');
        }
    }
}

// Notification System
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
