"""
🌸 若曦V2 JWT认证系统
安全的用户身份验证与授权
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config_manager import config
from core.exceptions import UnauthorizedException
from core.log_manager import get_logger

logger = get_logger(__name__)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token安全
security = HTTPBearer()


class TokenData(BaseModel):
    """Token数据模型"""

    user_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None


class UserAuth(BaseModel):
    """用户认证模型"""

    user_id: str
    username: str
    email: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class JWTAuthManager:
    """
    JWT认证管理器

    功能:
    - Token生成与验证
    - 密码哈希与验证
    - 用户会话管理
    """

    def __init__(self):
        # 从配置获取密钥或使用默认
        self.secret_key = config.get(
            "security.jwt_secret", "your-secret-key-change-in-production"
        )
        self.algorithm = config.get("security.jwt_algorithm", "HS256")
        self.access_token_expire_minutes = config.get(
            "security.access_token_expire_minutes", 1440
        )  # 24小时

        # 内存用户存储 (生产环境使用数据库)
        self.users_db: Dict[str, Dict] = {}
        self.token_blacklist: set = set()

    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问Token

        Args:
            data: 要编码到token的数据
            expires_delta: 过期时间增量

        Returns:
            JWT token字符串
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.info(f"🔑 Token创建 | 用户: {data.get('sub', 'unknown')}")

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        验证Token

        Args:
            token: JWT token字符串

        Returns:
            TokenData或None
        """
        # 检查黑名单
        if token in self.token_blacklist:
            logger.warning("⛔ Token已在黑名单中")
            return None

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id: str = payload.get("sub")
            username: str = payload.get("username")

            if user_id is None:
                return None

            token_data = TokenData(user_id=user_id, username=username)
            return token_data

        except JWTError as e:
            logger.warning(f"⚠️ Token验证失败: {e}")
            return None

    def register_user(
        self, username: str, email: str, password: str, user_id: Optional[str] = None
    ) -> UserAuth:
        """
        注册新用户

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            user_id: 可选的用户ID

        Returns:
            新用户信息
        """
        import uuid

        # 检查用户名是否已存在
        for user in self.users_db.values():
            if user["username"] == username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
                )
            if user["email"] == email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册"
                )

        # 生成用户ID
        new_user_id = user_id or str(uuid.uuid4())[:12]

        # 创建用户
        self.users_db[new_user_id] = {
            "user_id": new_user_id,
            "username": username,
            "email": email,
            "hashed_password": self._hash_password(password),
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

        logger.info(f"👤 用户注册 | {username} ({new_user_id})")

        return UserAuth(
            user_id=new_user_id,
            username=username,
            email=email,
            is_active=True,
            created_at=datetime.utcnow(),
        )

    def authenticate_user(self, username: str, password: str) -> Optional[UserAuth]:
        """
        认证用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            用户信息或None
        """
        # 查找用户
        user_data = None
        user_id = None

        for uid, user in self.users_db.items():
            if user["username"] == username:
                user_data = user
                user_id = uid
                break

        if not user_data:
            logger.warning(f"⛔ 认证失败: 用户不存在 | {username}")
            return None

        # 验证密码
        if not self._verify_password(password, user_data["hashed_password"]):
            logger.warning(f"⛔ 认证失败: 密码错误 | {username}")
            return None

        # 检查用户是否激活
        if not user_data.get("is_active", True):
            logger.warning(f"⛔ 认证失败: 用户已禁用 | {username}")
            return None

        logger.info(f"✅ 用户认证成功 | {username}")

        return UserAuth(
            user_id=user_id,
            username=user_data["username"],
            email=user_data.get("email"),
            is_active=user_data.get("is_active", True),
        )

    def logout(self, token: str) -> bool:
        """
        用户登出 (将token加入黑名单)

        Args:
            token: 要注销的token

        Returns:
            是否成功
        """
        self.token_blacklist.add(token)
        logger.info("🚪 用户登出 | Token已加入黑名单")
        return True

    def cleanup_expired_tokens(self):
        """清理过期的黑名单token (定期执行)"""
        # 实际实现中应该检查token的exp字段
        logger.debug("清理黑名单token")


# 全局认证管理器实例
auth_manager = JWTAuthManager()


# ========== FastAPI依赖 ==========


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserAuth:
    """
    获取当前用户 (FastAPI依赖)

    使用方式:
    ```python
    @app.get("/protected")
    async def protected_endpoint(user: UserAuth = Depends(get_current_user)):
        return {"message": f"Hello {user.username}"}
    ```
    """
    token = credentials.credentials

    token_data = auth_manager.verify_token(token)

    if token_data is None:
        raise UnauthorizedException("无效的认证token")

    # 获取用户信息
    user_data = auth_manager.users_db.get(token_data.user_id)

    if user_data is None:
        raise UnauthorizedException("用户不存在")

    if not user_data.get("is_active", True):
        raise UnauthorizedException("用户已被禁用")

    return UserAuth(
        user_id=token_data.user_id,
        username=token_data.username or user_data["username"],
        email=user_data.get("email"),
        is_active=user_data.get("is_active", True),
    )


async def get_current_active_user(
    user: UserAuth = Depends(get_current_user),
) -> UserAuth:
    """获取当前活跃用户"""
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return user


# ========== 可选认证依赖 ==========


async def optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[UserAuth]:
    """可选认证 - 未登录返回None而非报错"""
    try:
        return await get_current_user(credentials)
    except:
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 JWT认证测试")
    print("=" * 60)

    # 注册测试用户
    print("\n【注册测试用户】")
    user = auth_manager.register_user(
        username="test_user", email="test@example.com", password="secure_password123"
    )
    print(f"  注册成功: {user.username} ({user.user_id})")

    # 测试认证
    print("\n【认证测试】")
    authenticated = auth_manager.authenticate_user("test_user", "secure_password123")
    if authenticated:
        print(f"  认证成功: {authenticated.username}")

    print("\n【Token创建与验证】")
    # 创建token
    token = auth_manager.create_access_token(
        data={"sub": user.user_id, "username": user.username}
    )
    print(f"  Token创建成功: {token[:50]}...")

    # 验证token
    verified = auth_manager.verify_token(token)
    if verified:
        print(f"  Token验证成功: {verified.username}")

    print("\n【错误测试】")
    # 错误密码
    wrong_auth = auth_manager.authenticate_user("test_user", "wrong_password")
    print(f"  错误密码认证: {'失败' if wrong_auth is None else '成功'}")

    # 无效token
    invalid_verify = auth_manager.verify_token("invalid_token_here")
    print(f"  无效Token验证: {'失败' if invalid_verify is None else '成功'}")

    print("\n" + "=" * 60)
    print("✅ JWT认证测试完成")
    print("安装依赖: pip install python-jose[cryptography] passlib[bcrypt]")
    print("=" * 60)
