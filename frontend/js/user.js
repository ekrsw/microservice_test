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

// ユーザー情報を画面に表示する関数
function displayUserInfo(userData) {
    const userInfoElement = document.getElementById('user-info');
    
    if (userData && userData.id && userData.username) {
        userInfoElement.innerHTML = `
            <div class="user-details">
                <p><strong>ユーザーID:</strong> ${userData.id}</p>
                <p><strong>ユーザー名:</strong> ${userData.username}</p>
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
