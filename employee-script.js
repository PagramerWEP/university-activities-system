// Check Authentication
window.addEventListener('DOMContentLoaded', () => {
    const user = apiGetCurrentUser();
    
    if (!user || user.role !== 'employee') {
        window.location.href = 'index.html';
        return;
    }
    
    // Display user name
    document.getElementById('employeeName').textContent = user.fullName;
    
    // Load theme
    const savedTheme = localStorage.getItem('selectedTheme') || 'black';
    document.body.className = `dashboard-body theme-${savedTheme}`;
    
    // Load statistics
    updateStatistics();
    
    // Load applications
    loadApplications();
    
    // Load sent requests
    loadSentRequests();
});

// Theme Management
function changeTheme(theme) {
    document.body.className = `dashboard-body theme-${theme}`;
    localStorage.setItem('selectedTheme', theme);
    showNotification('تم تغيير الثيم بنجاح', 'success');
}

// Logout
function logout() {
    apiLogout();
    window.location.href = 'index.html';
}

// Helper function to get application by ID
function getApplicationById(applicationId) {
    return allApplications.find(app => app.id == applicationId);
}

// Update Statistics
async function updateStatistics() {
    const apiResult = await apiGetStatistics();
    
    if (apiResult.success && apiResult.statistics) {
        const stats = apiResult.statistics;
        document.getElementById('pendingCount').textContent = stats.pending;
        document.getElementById('approvedCount').textContent = stats.approved;
        document.getElementById('rejectedCount').textContent = stats.rejected;
        document.getElementById('totalCount').textContent = stats.total;
    } else {
        document.getElementById('pendingCount').textContent = '0';
        document.getElementById('approvedCount').textContent = '0';
        document.getElementById('rejectedCount').textContent = '0';
        document.getElementById('totalCount').textContent = '0';
    }
}

// Load and Display Applications
let allApplications = [];
let currentApplicationId = null;

async function loadApplications() {
    console.log('Loading applications...');
    const apiResult = await apiGetAllApplications();
    
    if (apiResult.success && apiResult.applications) {
        allApplications = apiResult.applications;
        console.log('Applications loaded:', allApplications.length);
    } else {
        allApplications = [];
        console.log('No applications found or error:', apiResult.message);
    }
    
    filterApplications();
}

function filterApplications() {
    const activityFilter = document.getElementById('activityFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = allApplications;
    
    // Filter by activity type
    if (activityFilter) {
        filtered = filtered.filter(app => app.activityType === activityFilter);
    }
    
    // Filter by status
    if (statusFilter) {
        filtered = filtered.filter(app => app.status === statusFilter);
    }
    
    // Filter by search query
    if (searchQuery) {
        filtered = filtered.filter(app => 
            app.studentName.toLowerCase().includes(searchQuery)
        );
    }
    
    displayApplications(filtered);
}

function displayApplications(applications) {
    const container = document.getElementById('applicationsList');
    
    if (applications.length === 0) {
        container.innerHTML = `
            <div class="application-item">
                <p style="text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-inbox"></i> لا توجد طلبات
                </p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = applications.map(app => `
        <div class="application-row clickable-row" data-app-id="${app.id}" role="button" tabindex="0" style="cursor: pointer;">
            <div class="app-row-header">
                <h4><i class="fas fa-user"></i> ${app.studentName}</h4>
                <span class="status-badge status-${app.status === 'قيد الانتظار' ? 'pending' : app.status === 'مقبول' ? 'approved' : 'rejected'}">
                    ${app.status}
                </span>
            </div>
            <div class="app-row-content">
                <div class="app-detail-item">
                    <strong><i class="fas fa-clipboard"></i> نوع النشاط:</strong>
                    ${app.activityType}
                </div>
                <div class="app-detail-item">
                    <strong><i class="fas fa-hashtag"></i> رقم النشاط:</strong>
                    ${app.activityNumber}
                </div>
                <div class="app-detail-item">
                    <strong><i class="fas fa-university"></i> الكلية:</strong>
                    ${app.college}
                </div>
                <div class="app-detail-item">
                    <strong><i class="fas fa-phone"></i> الهاتف:</strong>
                    ${app.phone}
                </div>
                <div class="app-detail-item">
                    <strong><i class="fas fa-calendar"></i> تاريخ التقديم:</strong>
                    ${new Date(app.submittedAt).toLocaleDateString('ar-IQ')}
                </div>
            </div>
        </div>
    `).join('');
    
    // Add event listeners for mobile compatibility
    let touchHandled = false;
    
    console.log('Adding event listeners to', container.querySelectorAll('.clickable-row').length, 'rows');
    
    container.querySelectorAll('.clickable-row').forEach((row, index) => {
        const handleClick = (e) => {
            console.log('Click event on row', index);
            if (touchHandled) {
                touchHandled = false;
                return;
            }
            const appId = row.getAttribute('data-app-id');
            console.log('Row clicked, app ID:', appId);
            showApplicationDetails(appId);
        };
        
        row.addEventListener('touchstart', () => {
            console.log('Touch start on row', index);
            touchHandled = false;
        });
        
        row.addEventListener('touchend', (e) => {
            console.log('Touch end on row', index);
            e.preventDefault();
            touchHandled = true;
            const appId = row.getAttribute('data-app-id');
            console.log('Row touched, app ID:', appId);
            showApplicationDetails(appId);
        });
        
        row.addEventListener('click', handleClick);
    });
}

// Show Application Details
function showApplicationDetails(applicationId) {
    console.log('showApplicationDetails called with ID:', applicationId);
    currentApplicationId = applicationId;
    const app = getApplicationById(applicationId);
    
    if (!app) {
        console.log('Application not found for ID:', applicationId);
        return;
    }
    
    console.log('Application found:', app);
    
    const detailsContent = document.getElementById('applicationDetails');
    detailsContent.innerHTML = `
        <div class="detail-row">
            <div class="detail-label">اسم الطالب:</div>
            <div class="detail-value">${app.studentName}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">نوع النشاط:</div>
            <div class="detail-value">${app.activityType}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">رقم النشاط:</div>
            <div class="detail-value">${app.activityNumber}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">الكلية:</div>
            <div class="detail-value">${app.college}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">القسم:</div>
            <div class="detail-value">${app.department}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">التخصص:</div>
            <div class="detail-value">${app.specialization}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">رقم الهاتف:</div>
            <div class="detail-value">${app.phone}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">تفاصيل إضافية:</div>
            <div class="detail-value">${app.details || 'لا توجد تفاصيل إضافية'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">الحالة:</div>
            <div class="detail-value">
                <span class="status-badge status-${app.status === 'قيد الانتظار' ? 'pending' : app.status === 'مقبول' ? 'approved' : 'rejected'}">
                    ${app.status}
                </span>
            </div>
        </div>
        <div class="detail-row">
            <div class="detail-label">تاريخ التقديم:</div>
            <div class="detail-value">${new Date(app.submittedAt).toLocaleString('ar-IQ')}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">آخر تحديث:</div>
            <div class="detail-value">${new Date(app.updatedAt).toLocaleString('ar-IQ')}</div>
        </div>
    `;
    
    document.getElementById('detailsModal').classList.add('active');
}

function closeDetailsModal() {
    document.getElementById('detailsModal').classList.remove('active');
    currentApplicationId = null;
}

// Approve Application
async function approveApplication() {
    if (!currentApplicationId) return;
    
    const result = await apiUpdateApplicationStatus(currentApplicationId, 'مقبول');
    
    if (result.success) {
        showNotification(result.message, 'success');
        closeDetailsModal();
        updateStatistics();
        loadApplications();
    } else {
        showNotification(result.message || 'حدث خطأ في قبول الطلب', 'error');
    }
}

// Reject Application
async function rejectApplication() {
    if (!currentApplicationId) return;
    
    const result = await apiUpdateApplicationStatus(currentApplicationId, 'مرفوض');
    
    if (result.success) {
        showNotification(result.message, 'success');
        closeDetailsModal();
        updateStatistics();
        loadApplications();
    } else {
        showNotification(result.message || 'حدث خطأ في رفض الطلب', 'error');
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

// Close modal on outside click
document.getElementById('detailsModal').addEventListener('click', (e) => {
    if (e.target.id === 'detailsModal') {
        closeDetailsModal();
    }
});

// ==================== EMPLOYEE REQUEST FUNCTIONS ====================

let sentRequests = [];

// Load Sent Requests
async function loadSentRequests() {
    const result = await apiGetEmployeeSentRequests();
    
    if (result.success && result.requests) {
        sentRequests = result.requests;
        displaySentRequests(sentRequests);
    } else {
        document.getElementById('sentRequestsList').innerHTML = `
            <div class="application-item">
                <p style="text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-inbox"></i> لا توجد طلبات مرسلة
                </p>
            </div>
        `;
    }
}

// Display Sent Requests
function displaySentRequests(requests) {
    const container = document.getElementById('sentRequestsList');
    
    if (requests.length === 0) {
        container.innerHTML = `
            <div class="application-item">
                <p style="text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-inbox"></i> لا توجد طلبات مرسلة
                </p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = requests.map(req => `
        <div class="application-row">
            <div class="app-row-header">
                <h4><i class="fas fa-envelope"></i> ${req.title}</h4>
                <span class="status-badge status-${req.status === 'قيد الانتظار' ? 'pending' : req.status === 'مقبول' ? 'approved' : 'rejected'}">
                    ${req.status}
                </span>
            </div>
            <div class="app-row-content">
                <div class="app-detail-item">
                    <strong><i class="fas fa-tag"></i> نوع الطلب:</strong>
                    ${req.requestType}
                </div>
                <div class="app-detail-item">
                    <strong><i class="fas fa-user"></i> الطالب:</strong>
                    ${req.studentName || 'جميع الطلاب'}
                </div>
                ${req.activityName ? `
                <div class="app-detail-item">
                    <strong><i class="fas fa-calendar-alt"></i> النشاط:</strong>
                    ${req.activityName}
                </div>
                ` : ''}
                ${req.deadline ? `
                <div class="app-detail-item">
                    <strong><i class="fas fa-clock"></i> الموعد النهائي:</strong>
                    ${new Date(req.deadline).toLocaleString('ar-IQ')}
                </div>
                ` : ''}
                <div class="app-detail-item">
                    <strong><i class="fas fa-calendar"></i> تاريخ الإرسال:</strong>
                    ${new Date(req.createdAt).toLocaleString('ar-IQ')}
                </div>
                ${req.responseMessage ? `
                <div class="app-detail-item" style="grid-column: 1 / -1;">
                    <strong><i class="fas fa-comment"></i> رد الطالب:</strong>
                    ${req.responseMessage}
                </div>
                ` : ''}
            </div>
            <div class="app-row-footer" style="margin-top: 10px;">
                <p style="color: var(--text-secondary); font-size: 0.9rem;">
                    <i class="fas fa-align-left"></i> ${req.description}
                </p>
            </div>
        </div>
    `).join('');
}

// Open Send Request Modal
function openSendRequestModal() {
    document.getElementById('sendRequestModal').classList.add('active');
}

// Close Send Request Modal
function closeSendRequestModal() {
    document.getElementById('sendRequestModal').classList.remove('active');
    document.getElementById('sendRequestForm').reset();
}

// Submit Employee Request
async function submitEmployeeRequest(event) {
    event.preventDefault();
    
    const requestData = {
        requestType: document.getElementById('requestType').value,
        title: document.getElementById('requestTitle').value,
        description: document.getElementById('requestDescription').value,
        activityName: document.getElementById('requestActivityName').value || null,
        activityCode: document.getElementById('requestActivityCode').value || null,
        deadline: document.getElementById('requestDeadline').value || null,
        studentId: null // General request to all students
    };
    
    const result = await apiSendEmployeeRequest(requestData);
    
    if (result.success) {
        showNotification('تم إرسال الطلب بنجاح', 'success');
        closeSendRequestModal();
        loadSentRequests();
    } else {
        showNotification(result.message || 'حدث خطأ في إرسال الطلب', 'error');
    }
}

// Close modal on outside click
document.getElementById('sendRequestModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'sendRequestModal') {
        closeSendRequestModal();
    }
});
