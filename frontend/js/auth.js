// 認証関連の処理を行うJavaScriptファイル

// APIのベースURL（実際の環境に合わせて変更してください）
const AUTH_API_URL = 'http://localhost:8001/api/v1/auth';
const USER_API_URL = 'http://localhost:8002/api/v1/user';

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
        // デモ用の簡易的なログイン処理
        // 実際の環境ではコメントを外してAPI呼び出しを行ってください
        if (username === 'testuser' && password === 'password') {
            // JWTトークンのペイロード部分（実際のトークンではこれは暗号化・署名されます）
            const mockPayload = {
                user_id: "550e8400-e29b-41d4-a716-446655440000", // UUIDフォーマット
                exp: Math.floor(Date.now() / 1000) + 3600,
                iat: Math.floor(Date.now() / 1000)
            };
            
            // Base64エンコードしたペイロードを含むモックトークン
            const mockToken = 'header.' + btoa(JSON.stringify(mockPayload)) + '.signature';
            
            // 成功した場合のモックデータ
            const mockTokenData = {
                access_token: mockToken,
                refresh_token: 'mock_refresh_token_' + Date.now(),
                token_type: 'bearer'
            };
            
            // トークンをローカルストレージに保存
            localStorage.setItem('accessToken', mockTokenData.access_token);
            localStorage.setItem('refreshToken', mockTokenData.refresh_token);
            
            // ユーザー情報を取得
            await fetchUserInfo(mockTokenData.access_token, mockPayload.user_id);
            
            // ダッシュボードページにリダイレクト
            window.location.href = 'dashboard.html';
        } else {
            // 認証失敗
            throw new Error('ユーザー名またはパスワードが正しくありません。');
        }
        
        // 実際のAPI呼び出しの例:
        /*
        const response = await fetch(`${AUTH_API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'ログインに失敗しました');
        }
        
        const tokenData = await response.json();
        localStorage.setItem('accessToken', tokenData.access_token);
        localStorage.setItem('refreshToken', tokenData.refresh_token);
        
        // ユーザー情報を取得
        await fetchUserInfo(tokenData.access_token);
        
        // ダッシュボードページにリダイレクト
        window.location.href = 'dashboard.html';
        */
        
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

// ユーザー情報を取得する関数
async function fetchUserInfo(token, userId) {
    try {
        // 実際の環境では以下のコードを使用
        /*
        // まず/meエンドポイントからユーザー情報を取得
        const meResponse = await fetch(`${USER_API_URL}/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!meResponse.ok) {
            throw new Error('ユーザー情報の取得に失敗しました');
        }
        
        const userData = await meResponse.json();
        localStorage.setItem('userData', JSON.stringify(userData));
        */
        
        // デモ用のモックデータ
        // トークンのペイロードからuser_idを取得し、そのIDに一致するユーザー情報を表示
        const mockUserData = {
            id: userId, // トークンのペイロードから取得したuser_id
            username: 'testuser',
            full_name: 'テストユーザー',
            email: 'testuser@example.com'
        };
        
        localStorage.setItem('userData', JSON.stringify(mockUserData));
    } catch (error) {
        console.error('ユーザー情報取得エラー:', error);
        throw error;
    }
}
