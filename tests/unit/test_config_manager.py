"""
🌸 若曦V2 配置管理器单元测试
目标: 验证配置加载、获取、重载功能
"""

import os

# 导入被测试模块
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from config_manager import ConfigManager, config


class TestConfigManager:
    """配置管理器测试类"""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """每个测试前重置配置单例"""
        yield
        # 清理
        ConfigManager._instance = None
        ConfigManager._config = {}

    def test_singleton_pattern(self):
        """测试单例模式 - 多个实例应返回同一对象"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_default_config_values(self):
        """测试默认配置值"""
        cfg = ConfigManager()

        # 应用配置
        assert cfg.get("app.name") == "若曦V2"
        assert cfg.get("app.version") == "2.0.0"
        assert cfg.get("app.debug") == False

        # AI配置
        assert cfg.get("ai.default_model") == "gemini-2.0-flash"
        assert cfg.get("ai.max_tokens") == 4096
        assert cfg.get("ai.temperature") == 0.7

        # 数据库配置
        assert cfg.get("database.type") == "sqlite"
        assert "ruoxi.db" in cfg.get("database.path")

    def test_env_override(self):
        """测试环境变量覆盖"""
        with patch.dict(
            os.environ,
            {
                "RUOXI_DEBUG": "true",
                "RUOXI_LOG_LEVEL": "DEBUG",
                "RUOXI_AI_MODEL": "custom-model",
            },
        ):
            cfg = ConfigManager()
            assert cfg.get("app.debug") == True
            assert cfg.get("log.level") == "DEBUG"
            assert cfg.get("ai.default_model") == "custom-model"

    def test_get_with_default(self):
        """测试带默认值的获取"""
        cfg = ConfigManager()

        # 存在的键
        assert cfg.get("app.name") == "若曦V2"

        # 不存在的键，有默认值
        assert cfg.get("nonexistent.key", "default") == "default"

        # 不存在的键，无默认值
        assert cfg.get("nonexistent.key") is None

    def test_nested_config_access(self):
        """测试嵌套配置访问"""
        cfg = ConfigManager()

        # 多层嵌套
        assert cfg.get("app.name") == "若曦V2"
        assert cfg.get("ai.timeout") == 30
        assert cfg.get("memory.short_term_limit") == 10

    def test_reload_config(self):
        """测试配置重载"""
        cfg = ConfigManager()
        original_value = cfg.get("app.name")

        # 重载
        cfg.reload()

        # 验证值仍然正确
        assert cfg.get("app.name") == original_value

    def test_get_all_config(self):
        """测试获取完整配置"""
        cfg = ConfigManager()
        all_config = cfg.get_all()

        assert isinstance(all_config, dict)
        assert "app" in all_config
        assert "ai" in all_config
        assert "database" in all_config


class TestConfigEdgeCases:
    """边界情况和异常处理测试"""

    def test_empty_key(self):
        """测试空键获取"""
        cfg = ConfigManager()
        assert cfg.get("") is None

    def test_invalid_nested_key(self):
        """测试无效嵌套键"""
        cfg = ConfigManager()
        # 中间键不存在
        assert cfg.get("nonexistent.nested.key") is None
        # 返回默认值
        assert cfg.get("nonexistent.nested.key", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
