"""
🌸 若曦V2 - PyTest配置
测试 fixtures 和配置
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "test_user_001"


@pytest.fixture
def sample_timestamp():
    """示例时间戳"""
    return datetime.utcnow()


# 异步fixture支持
@pytest.fixture
def async_fixture():
    """异步 fixture 装饰器"""
    def decorator(func):
        return pytest.fixture(func)
    return decorator


# 测试数据目录
@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    data_dir = PROJECT_ROOT / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir
