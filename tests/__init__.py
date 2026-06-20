"""
🌸 若曦V2 测试套件
确保代码质量，目标80%+覆盖率
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 测试环境配置
os.environ.setdefault("RUOXI_ENV", "testing")
os.environ.setdefault("RUOXI_LOG_LEVEL", "DEBUG")
os.environ.setdefault("RUOXI_DB_TYPE", "sqlite")
os.environ.setdefault("RUOXI_DB_PATH", "data/test.db")
