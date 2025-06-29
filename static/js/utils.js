/**
 * AIDE-X 共通ユーティリティ
 */

// HTMLサニタイズ
function sanitizeHtml(text) {
    if (typeof text !== 'string') {
        text = String(text);
    }
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// CSRFトークンを取得
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// URLから構造IDを取得
function getStructureIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

// 通知を表示
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// グローバルスコープに公開
window.utils = {
    sanitizeHtml,
    getCSRFToken,
    getStructureIdFromUrl,
    showNotification
}; 