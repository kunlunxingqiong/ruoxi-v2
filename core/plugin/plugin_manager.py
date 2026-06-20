"""
🌸 若曦V2 - 插件管理器
支持第三方扩展若曦功能
"""
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
from pathlib import Path
import importlib.util
import asyncio
import json


class PluginType(Enum):
    """插件类型"""
    HEALTH_PROVIDER = auto()
    AI_MODEL = auto()
    EMOTION_ANALYZER = auto()
    NOTIFICATION = auto()
    DATA_SOURCE = auto()
    CUSTOM = auto()


class HookPoint(Enum):
    """钩子点"""
    BEFORE_CHAT = auto()
    AFTER_CHAT = auto()
    BEFORE_HEALTH_ANALYSIS = auto()
    AFTER_HEALTH_ANALYSIS = auto()
    ON_EMOTION_DETECTED = auto()
    ON_MEMORY_STORED = auto()
    SCHEDULED_TASK = auto()


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict = field(default_factory=dict)
    hooks: List[HookPoint] = field(default_factory=list)


class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self.config: Dict = {}
        self.enabled: bool = False
    
    @abstractmethod
    async def initialize(self, config: Dict) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """关闭插件"""
        pass
    
    async def on_hook(self, hook_point: HookPoint, context: Dict) -> Dict:
        """钩子回调 - 可被覆盖"""
        return context


@dataclass
class PluginRegistry:
    """插件注册信息"""
    plugin: BasePlugin
    metadata: PluginMetadata
    instance: Any = None


class PluginManager:
    """
    插件管理器
    
    功能:
    - 动态加载插件
    - 钩子系统
    - 插件依赖管理
    - 热插拔
    """
    
    def __init__(self):
        self._plugins: Dict[str, PluginRegistry] = {}
        self._hooks: Dict[HookPoint, List[Callable]] = {hook: [] for hook in HookPoint}
        self._plugin_dir = Path("plugins")
    
    async def discover_plugins(self) -> List[PluginMetadata]:
        """发现可用插件"""
        discovered = []
        
        if not self._plugin_dir.exists():
            return discovered
        
        for plugin_file in self._plugin_dir.glob("*/plugin.py"):
            try:
                metadata = await self._load_metadata(plugin_file.parent)
                discovered.append(metadata)
            except Exception as e:
                print(f"发现插件失败 {plugin_file}: {e}")
        
        return discovered
    
    async def load_plugin(self, plugin_name: str, config: Dict = None) -> bool:
        """加载插件"""
        if plugin_name in self._plugins:
            print(f"插件 {plugin_name} 已加载")
            return False
        
        plugin_path = self._plugin_dir / plugin_name / "plugin.py"
        if not plugin_path.exists():
            print(f"插件文件不存在: {plugin_path}")
            return False
        
        try:
            # 动态导入
            spec = importlib.util.spec_from_file_location(
                f"plugin.{plugin_name}", 
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取插件类
            plugin_class = getattr(module, "Plugin", None)
            if not plugin_class:
                print(f"插件 {plugin_name} 未定义 Plugin 类")
                return False
            
            # 实例化
            plugin = plugin_class()
            
            # 加载元数据
            metadata = await self._load_metadata(self._plugin_dir / plugin_name)
            plugin.metadata = metadata
            
            # 初始化
            if config is None:
                config = await self._load_plugin_config(plugin_name)
            
            success = await plugin.initialize(config)
            if not success:
                print(f"插件 {plugin_name} 初始化失败")
                return False
            
            plugin.enabled = True
            plugin.config = config
            
            # 注册
            self._plugins[plugin_name] = PluginRegistry(
                plugin=plugin,
                metadata=metadata
            )
            
            # 注册钩子
            for hook in metadata.hooks:
                self._hooks[hook].append(plugin)
            
            print(f"✅ 插件 {plugin_name} v{metadata.version} 加载成功")
            return True
            
        except Exception as e:
            print(f"加载插件 {plugin_name} 失败: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self._plugins:
            return False
        
        registry = self._plugins[plugin_name]
        
        # 注销钩子
        for hook in registry.metadata.hooks:
            if registry.plugin in self._hooks[hook]:
                self._hooks[hook].remove(registry.plugin)
        
        # 关闭插件
        await registry.plugin.shutdown()
        
        # 移除
        del self._plugins[plugin_name]
        
        print(f"✅ 插件 {plugin_name} 已卸载")
        return True
    
    async def execute_hook(
        self, 
        hook_point: HookPoint, 
        context: Dict
    ) -> Dict:
        """执行钩子链"""
        current_context = context.copy()
        
        for plugin in self._hooks[hook_point]:
            if not plugin.enabled:
                continue
            
            try:
                result = await plugin.on_hook(hook_point, current_context)
                if result:
                    current_context.update(result)
            except Exception as e:
                print(f"钩子执行失败 {plugin.metadata.name}: {e}")
        
        return current_context
    
    async def _load_metadata(self, plugin_dir: Path) -> PluginMetadata:
        """加载插件元数据"""
        metadata_file = plugin_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"插件元数据不存在: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PluginMetadata(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=PluginType[data.get("type", "CUSTOM")],
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema", {}),
            hooks=[HookPoint[h] for h in data.get("hooks", [])]
        )
    
    async def _load_plugin_config(self, plugin_name: str) -> Dict:
        """加载插件配置"""
        config_file = self._plugin_dir / plugin_name / "config.json"
        
        if not config_file.exists():
            return {}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_loaded_plugins(self) -> List[PluginMetadata]:
        """获取已加载插件列表"""
        return [r.metadata for r in self._plugins.values()]
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        registry = self._plugins.get(name)
        return registry.plugin if registry else None


# 全局插件管理器
plugin_manager = PluginManager()
