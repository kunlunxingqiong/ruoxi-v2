"""
🌸 若曦V2 认证API
用户注册、登录、登出
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from core.log_manager import get_logger
from core.exceptions import ValidationException
from ...core_auth import auth_manager, get_current_user, optional_current_user, UserAuth

logger = get_logger(__name__)

router = APIRouter()


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: UserAuth


class UserProfile(BaseModel):
    """用户资料"""
    user_id: str
    username: str
    email: Optional[str]
    is_active: bool
    created_at: Optional[str]


@router.post("/register", response_model=UserProfile)
async def register(user_data: UserRegister):
    """
    用户注册
    
    创建新账号开始使用若曦
    
    **请求示例:**
    ```json
    {
        "username": "xiaoming",
        "email": "xiaoming@example.com",
        "password": "secure_password123"
    }
    ```
    
    **响应示例:**
    ```json
    {
        "user_id": "usr_abc123",
        "username": "xiaoming",
        "email": "xiaoming@example.com",
        "is_active": true,
        "created_at": "2026-06-21T03:15:00"
    }
    ```
    """
    # 验证用户名
    if not user_data.username.isalnum():
        raise ValidationException("用户名只能包含字母和数字")
    
    # 注册用户
    new_user = auth_manager.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    
    logger.info(f"👤 新用户注册 | {new_user.username}")
    
    return UserProfile(
        user_id=new_user.user_id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """
    用户登录
    
    获取访问Token
    
    **请求示例:**
    ```json
    {
        "username": "xiaoming",
        "password": "secure_password123"
    }
    ```
    
    **响应示例:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "user_id": "usr_abc123",
            "username": "xiaoming",
            "email": "xiaoming@example.com",
            "is_active": true
        }
    }
    ```
    """
    # 验证用户
    user = auth_manager.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建token
    access_token = auth_manager.create_access_token(
        data={"sub": user.user_id, "username": user.username}
    )
    
    logger.info(f"✅ 用户登录 | {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=auth_manager.access_token_expire_minutes * 60,
        user=user
    )


@router.post("/logout")
async def logout(user: UserAuth = Depends(get_current_user)):
    """
    用户登出
    
    使当前Token失效
    """
    # TODO: 将token加入黑名单
    # 需要实现token存储和黑名单机制
    logger.info(f"🚪 用户登出 | {user.username}")
    
    return {
        "success": True,
        "message": "登出成功",
        "user_id": user.user_id
    }


@router.get("/me", response_model=UserProfile)
async def get_me(user: UserAuth = Depends(get_current_user)):
    """
    获取当前用户信息
    
    需要登录Token
    """
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None
    )


@router.put("/me")
async def update_me(
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    user: UserAuth = Depends(get_current_user)
):
    """
    更新用户信息
    
    可以修改用户名和邮箱
    """
    # 获取用户数据
    user_data = auth_manager.users_db.get(user.user_id)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    if username:
        user_data["username"] = username
    if email:
        user_data["email"] = email
    
    logger.info(f"✏️ 用户资料更新 | {user.user_id}")
    
    return UserProfile(
        user_id=user.user_id,
        username=user_data["username"],
        email=user_data.get("email"),
        is_active=user_data.get("is_active", True),
        created_at=user_data.get("created_at").isoformat() if user_data.get("created_at") else None
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str = Field(..., min_length=8, max_length=128),
    user: UserAuth = Depends(get_current_user)
):
    """
    修改密码
    
    需要提供当前密码进行验证
    """
    # 验证旧密码
    auth_result = auth_manager.authenticate_user(user.username, old_password)
    
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user_data = auth_manager.users_db.get(user.user_id)
    user_data["hashed_password"] = auth_manager._hash_password(new_password)
    
    logger.info(f"🔐 用户密码修改 | {user.username}")
    
    return {
        "success": True,
        "message": "密码修改成功，请重新登录"
    }


@router.get("/refresh")
async def refresh_token(user: UserAuth = Depends(get_current_user)):
    """
    刷新Token
    
    获取新的访问Token (延长登录时间)
    """
    # 创建新token
    new_token = auth_manager.create_access_token(
        data={"sub": user.user_id, "username": user.username}
    )
    
    logger.info(f"🔄 Token刷新 | {user.username}")
    
    return TokenResponse(
        access_token=new_token,
        expires_in=auth_manager.access_token_expire_minutes * 60,
        user=user
    )


@router.post("/forgot-password")
async def forgot_password(username: str):
    """
    忘记密码
    
    发送密码重置邮件 (开发中)
    """
    # TODO: 实现邮件发送功能
    logger.info(f"📧 密码重置请求 | {username}")
    
    return {
        "success": True,
        "message": "密码重置邮件已发送 (开发中功能)"
    }
