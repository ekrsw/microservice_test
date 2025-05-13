// 認証関連の処理を行うJavaScriptファイル

// APIのベースURL（実際の環境に合わせて変更してください）
// const AUTH_API_URL = 'http://localhost:8000/api/v1/auth'; // 本来のAPI URL

// DOMが読み込まれたら実行
document.addEventListener('DOMContentLoaded', () => {
    // すでにログイン済みの場合はダッシュボードにリダイレクト
    if (isLoggedIn()) {
        window.location.href = 'dashboard.html';
        return;
    }

    // ログインフォームの送信イベントを処理
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

// ログイン処理
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('error-message');
    
    // 入力値の検証
    if (!username || !password) {
        errorMessage.textContent = 'ユーザー名とパスワードを入力してください。';
        return;
    }

    try {
        // モックのログイン処理（APIが利用できないため）
        if (username === 'testuser' && password === 'password') {
            // 成功した場合のモックデータ
            const mockTokenData = {
                access_token: 'mock_access_token_' + Date.now(),
                refresh_token: 'mock_refresh_token_' + Date.now(),
                token_type: 'bearer'
            };
            
            // ユーザーデータをモック
            const mockUserData = {
                id: 'user123',
                username: username,
                email: 'testuser@example.com'
            };
            
            // トークンとユーザーデータをローカルストレージに保存
            localStorage.setItem('accessToken', mockTokenData.access_token);
            localStorage.setItem('refreshToken', mockTokenData.refresh_token);
            localStorage.setItem('userData', JSON.stringify(mockUserData));
            
            // ダッシュボードページにリダイレクト
            window.location.href = 'dashboard.html';
        } else {
            // 認証失敗
            throw new Error('ユーザー名またはパスワードが正しくありません。');
        }
        
    } catch (error) {
        console.error('ログインエラー:', error);
        errorMessage.textContent = error.message || 'ログインに失敗しました。ユーザー名とパスワードを確認してください。';
    }
}

// ログアウト処理
function logout() {
    // ローカルストレージからトークンを削除
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userData');
    
    // ログインページにリダイレクト
    window.location.href = 'index.html';
}

// ログイン状態のチェック
function isLoggedIn() {
    return !!localStorage.getItem('accessToken');
}

// アクセストークンの取得
function getAccessToken() {
    return localStorage.getItem('accessToken');
}

// リフレッシュトークンの取得
function getRefreshToken() {
    return localStorage.getItem('refreshToken');
}
