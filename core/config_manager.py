"""
🌸 若曦V2 配置管理系统
统一配置管理，支持多环境和热重载
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConfigManager:
    """统一配置管理器"""

    _instance = None
    _config = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置"""
        if not self._config:
            self._load_config()

    def _load_config(self):
        """加载配置文件"""
        config_path = self._get_config_path()

        # 默认配置
        self._config = {
            "app": {
                "name": "若曦V2",
                "version": "2.0.0",
                "debug": False,
            },
            "ai": {
                "default_model": "gemini-2.0-flash",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30,
            },
            "memory": {
                "short_term_limit": 10,
                "long_term_enabled": True,
                "embedding_model": "local",
            },
            "database": {
                "type": "sqlite",
                "path": "data/ruoxi.db",
            },
            "log": {
                "level": "INFO",
                "format": "json",
                "max_size": "100MB",
                "backup_count": 7,
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "cors_origins": ["*"],
            },
        }

        # 从文件加载配置
        self._load_from_file(config_path)

        # 环境变量覆盖
        self._override_from_env()

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        env = os.getenv("RUOXI_ENV", "development")
        config_dir = Path(__file__).parent.parent / "config"

        # 按优先级查找配置文件
        candidates = [
            config_dir / f"config.{env}.yaml",
            config_dir / "config.yaml",
            config_dir / "config.json",
        ]

        for path in candidates:
            if path.exists():
                return path

        return config_dir / "config.yaml"

    def _load_from_file(self, path: Path):
        """从文件加载配置"""
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f)
                elif path.suffix == ".json":
                    file_config = json.load(f)
                else:
                    return

            if file_config:
                self._deep_merge(self._config, file_config)
        except Exception as e:
            print(f"[Config] 加载配置文件失败: {e}")

    def _override_from_env(self):
        """从环境变量覆盖配置"""
        env_mappings = {
            "RUOXI_DEBUG": ("app", "debug", bool),
            "RUOXI_LOG_LEVEL": ("log", "level", str),
            "RUOXI_AI_MODEL": ("ai", "default_model", str),
            "RUOXI_MAX_TOKENS": ("ai", "max_tokens", int),
            "RUOXI_DB_TYPE": ("database", "type", str),
            "RUOXI_DB_PATH": ("database", "path", str),
            "RUOXI_API_PORT": ("api", "port", int),
        }

        for env_key, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                try:
                    self._config[section][key] = type_func(value)
                except (ValueError, TypeError):
                    pass

    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键，支持点分隔 (如 "ai.default_model")
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()

    def reload(self):
        """重新加载配置"""
        self._config = {}
        self._load_config()

    def to_yaml(self) -> str:
        """导出为YAML格式"""
        return yaml.dump(self._config, allow_unicode=True, default_flow_style=False)

    def to_json(self, indent: int = 2) -> str:
        """导出为JSON格式"""
        return json.dumps(self._config, ensure_ascii=False, indent=indent)


# 全局配置实例
config = ConfigManager()


if __name__ == "__main__":
    # 测试配置管理器
    print("=" * 60)
    print("🌸 若曦V2 配置管理系统测试")
    print("=" * 60)

    print("\n【应用配置】")
    print(f"  名称: {config.get('app.name')}")
    print(f"  版本: {config.get('app.version')}")
    print(f"  调试: {config.get('app.debug')}")

    print("\n【AI配置】")
    print(f"  默认模型: {config.get('ai.default_model')}")
    print(f"  最大Token: {config.get('ai.max_tokens')}")
    print(f"  温度: {config.get('ai.temperature')}")

    print("\n【数据库配置】")
    print(f"  类型: {config.get('database.type')}")
    print(f"  路径: {config.get('database.path')}")

    print("\n【日志配置】")
    print(f"  级别: {config.get('log.level')}")
    print(f"  格式: {config.get('log.format')}")
