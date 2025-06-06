from contextlib import asynccontextmanager
import os
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import app_logger, get_request_logger
from app.db.init import Database
from app.messaging.rabbitmq import rabbitmq_client
from app.messaging.auth_handler import handle_user_creation_response


# ログディレクトリの作成（ファイルログが有効な場合）
if settings.LOG_TO_FILE:
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクルを管理"""
    # 起動の処理
    try:
        # データベース初期化
        db = Database()
        await db.init()
        app_logger.info("Database initialized successfully")
        
        # RabbitMQ初期化
        await rabbitmq_client.initialize()
        app_logger.info("RabbitMQ initialized successfully")
        
        # ユーザー作成レスポンスのコンシューマーをセットアップ
        await rabbitmq_client.setup_user_creation_response_consumer(handle_user_creation_response)
        app_logger.info("User creation response consumer setup successfully")
        
    except Exception as e:
        app_logger.error(f"Initialization failed: {str(e)}")
        raise
    
    yield # アプリケーションの実行中

    # シャットダウンの処理
    app_logger.info("Shutting down application...")
    
    # RabbitMQ接続のクローズ
    try:
        await rabbitmq_client.close()
        app_logger.info("RabbitMQ connection closed")
    except Exception as e:
        app_logger.error(f"Error closing RabbitMQ connection: {str(e)}")

# FastAPIアプリケーションの作成
app = FastAPI(
    title="認証サービス",
    description="ユーザー認証とトークン管理を提供するマイクロサービス",
    version="1.0.0",
    lifespan=lifespan
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンのみを許可するように変更する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストIDとロギングミドルウェア
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    # リクエストIDを生成
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # リクエストロガーの取得
    logger = get_request_logger(request)

    # リクエスト情報のロギング
    logger.info(
        f"Request started: {request.method} {request.url.path} "
        f"(Client: {request.client.host if request.client else 'unknown'})"
    )

    # 処理時間の計測
    start_time = time.time()

    try:
        # リクエスト処理
        response = await call_next(request)
        process_time = time.time() - start_time

        # レスポンスヘッダーの設定
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # レスポンス情報のロギング
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Process time: {process_time:.3f}s"
        )

        return response
    except Exception as e:
        # 例外発生時のロギング
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"Error: {str(e)} "
            f"Process time: {process_time:.3f}s",
            exc_info=True
        )
        raise


# バリデーションエラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # リクエストロガーの取得
    logger = get_request_logger(request)
    
    # エラー情報の処理（ValueErrorオブジェクトを文字列に変換）
    errors = []
    for error in exc.errors():
        # エラーのコピーを作成
        processed_error = error.copy()
        # ctx内のValueErrorオブジェクトを文字列に変換
        if 'ctx' in processed_error and 'error' in processed_error['ctx']:
            if isinstance(processed_error['ctx']['error'], ValueError):
                processed_error['ctx']['error'] = str(processed_error['ctx']['error'])
        errors.append(processed_error)
    
    # バリデーションエラーのロギング
    logger.warning(
        f"Validation error: {request.method} {request.url.path} "
        f"Errors: {errors}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "body": exc.body},
    )


# APIルーターの登録
app.include_router(api_router, prefix="/api/v1")

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "認証サービスAPI",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # アプリケーション起動時のログ
    app_logger.info(
        f"Starting auth-service in {settings.ENVIRONMENT} mode "
        f"(Log level: {settings.LOG_LEVEL})"
    )
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
