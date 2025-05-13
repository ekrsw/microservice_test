// ユーザー情報関連の処理を行うJavaScriptファイル

// DOMが読み込まれたら実行
document.addEventListener('DOMContentLoaded', () => {
    // ログイン状態をチェック
    if (!isLoggedIn()) {
        // ログインしていない場合はログインページにリダイレクト
        window.location.href = 'index.html';
        return;
    }

    // ユーザー情報を取得して表示
    fetchUserInfo();

    // ログアウトボタンのイベントリスナーを設定
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

// ユーザー情報を取得して表示する関数
async function fetchUserInfo() {
    const userInfoElement = document.getElementById('user-info');
    
    try {
        // ローカルストレージからユーザーデータを取得
        const cachedUserData = localStorage.getItem('userData');
        
        if (!cachedUserData) {
            throw new Error('ユーザー情報が見つかりません。');
        }
        
        const userData = JSON.parse(cachedUserData);
        
        // ユーザー情報を表示
        displayUserInfo(userData);
        
        // トークンからユーザー情報を再取得
        const token = getAccessToken();
        if (token) {
            await refreshUserInfo(token);
        }
        
    } catch (error) {
        console.error('ユーザー情報取得エラー:', error);
        userInfoElement.innerHTML = `
            <div class="error">
                <p>エラーが発生しました: ${error.message}</p>
                <button onclick="logout()">ログインページに戻る</button>
            </div>
        `;
    }
}

// APIからユーザー情報を再取得する関数
async function refreshUserInfo(token) {
    try {
        // JWTトークンからペイロードを取得
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
            throw new Error('無効なトークン形式です');
        }
        
        // Base64デコードしてペイロードを取得
        const payload = JSON.parse(atob(tokenParts[1]));
        const userId = payload.user_id;
        
        if (!userId) {
            throw new Error('トークンにユーザーIDが含まれていません');
        }
        
        const USER_API_URL = 'http://localhost:8002/api/v1/user';
        
        // /meエンドポイントからユーザー情報を取得
        const meResponse = await fetch(`${USER_API_URL}/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!meResponse.ok) {
            throw new Error('ユーザー情報の更新に失敗しました');
        }
        
        const userData = await meResponse.json();
        
        // ユーザーIDが一致することを確認
        if (userData.id !== userId) {
            console.warn('トークンのユーザーIDとAPIレスポンスのIDが一致しません');
        }
        
        localStorage.setItem('userData', JSON.stringify(userData));
        
        // 画面を更新
        displayUserInfo(userData);
    } catch (error) {
        console.error('ユーザー情報更新エラー:', error);
        // エラーが発生しても既存のデータで表示を続行
    }
}

// ユーザー情報を画面に表示する関数
function displayUserInfo(userData) {
    const userInfoElement = document.getElementById('user-info');
    
    if (userData && userData.id && userData.username) {
        userInfoElement.innerHTML = `
            <div class="user-details">
                <p><strong>ユーザーID:</strong> ${userData.id}</p>
                <p><strong>ユーザー名:</strong> ${userData.username}</p>
                ${userData.full_name ? `<p><strong>氏名:</strong> ${userData.full_name}</p>` : ''}
                ${userData.email ? `<p><strong>メールアドレス:</strong> ${userData.email}</p>` : ''}
            </div>
        `;
    } else {
        userInfoElement.innerHTML = `
            <div class="error">
                <p>ユーザー情報が不完全です。</p>
            </div>
        `;
    }
}

// アクセストークンの取得
function getAccessToken() {
    return localStorage.getItem('accessToken');
}

// ログイン状態のチェック
function isLoggedIn() {
    return !!localStorage.getItem('accessToken');
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
