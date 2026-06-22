"""
🌸 若曦V2 向量记忆存储
基于ChromaDB的语义记忆检索系统
"""

import hashlib
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from core.config_manager import config
from core.exceptions import MemoryException
from core.log_manager import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryItem:
    """记忆条目"""

    id: str
    content: str
    memory_type: str  # "conversation", "health", "emotion", "fact"
    user_id: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    importance: float = 1.0  # 重要度 0-1
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat() if self.created_at else None
        result["last_accessed"] = (
            self.last_accessed.isoformat() if self.last_accessed else None
        )
        return result


class EmbeddingService:
    """
    文本嵌入服务

    将文本转换为向量，用于语义搜索
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Args:
            model_name: 嵌入模型名称
                - paraphrase-multilingual-MiniLM-L12-v2: 多语言轻量版 (推荐)
                - all-MiniLM-L6-v2: 英文版
                - BAAI/bge-large-zh: 中文专用
        """
        self.model_name = model_name
        self.model = None
        self.is_available = False

        if EMBEDDINGS_AVAILABLE:
            try:
                self._load_model()
            except Exception as e:
                logger.warning(f"⚠️ 嵌入模型加载失败，将使用简化版: {e}")
        else:
            logger.info("📦 sentence-transformers未安装，使用简化嵌入")

    def _load_model(self):
        """加载嵌入模型"""
        logger.info(f"🔄 加载嵌入模型: {self.model_name}")

        # 使用缓存目录
        cache_dir = (
            Path(config.get("system.data_dir", "data")) / "models" / "embeddings"
        )
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.model = SentenceTransformer(self.model_name, cache_folder=str(cache_dir))
        self.is_available = True

        logger.info(
            f"✅ 嵌入模型加载完成 | 维度: {self.model.get_sentence_embedding_dimension()}"
        )

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        编码文本为向量

        Args:
            texts: 单个文本或文本列表

        Returns:
            向量列表
        """
        if isinstance(texts, str):
            texts = [texts]

        if self.is_available and self.model:
            try:
                embeddings = self.model.encode(texts, convert_to_list=True)
                return (
                    embeddings
                    if isinstance(embeddings[0], list)
                    else [embeddings.tolist()]
                )
            except Exception as e:
                logger.warning(f"⚠️ 嵌入编码失败，使用简化版: {e}")

        # 简化版：使用哈希模拟
        return self._simple_hash_embed(texts)

    def _simple_hash_embed(self, texts: List[str]) -> List[List[float]]:
        """简化版嵌入 (用于测试/备选)"""
        embeddings = []
        for text in texts:
            # 使用哈希生成固定维度向量
            hash_val = hashlib.md5(text.encode()).hexdigest()
            # 转换为128维向量 (每个字符2位十六进制)
            vec = [int(hash_val[i : i + 2], 16) / 255.0 for i in range(0, 64, 2)]
            # 扩展到384维 (与MiniLM一致)
            vec = vec * 6  # 128 * 3 = 384
            embeddings.append(vec[:384])

        return embeddings


class VectorMemoryStore:
    """
    向量记忆存储

    使用ChromaDB存储和检索语义记忆

    特性:
    - 语义相似度搜索
    - 多记忆类型分类
    - 基于时间的衰减
    - 重要性排序
    """

    def __init__(self, collection_name: str = "ruoxi_memories"):
        """
        Args:
            collection_name: ChromaDB集合名称
        """
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_service = EmbeddingService()
        self.is_available = False

        # 内存备选 (ChromaDB不可用时)
        self._memories: List[MemoryItem] = []

        if CHROMADB_AVAILABLE:
            try:
                self._init_chromadb()
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB初始化失败，使用内存模式: {e}")
        else:
            logger.info("📦 ChromaDB未安装，使用内存模式")

    def _init_chromadb(self):
        """初始化ChromaDB"""
        # 持久化目录
        persist_dir = Path(config.get("system.data_dir", "data")) / "chromadb"
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(persist_dir),
                anonymized_telemetry=False,
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
        )

        self.is_available = True
        logger.info(f"✅ ChromaDB初始化完成 | 集合: {self.collection_name}")

    def add_memory(self, item: MemoryItem) -> str:
        """
        添加记忆

        Args:
            item: 记忆条目

        Returns:
            记忆ID
        """
        # 生成嵌入向量
        embedding = self.embedding_service.encode(item.content)[0]

        if self.is_available:
            # 存入ChromaDB
            self.collection.add(
                ids=[item.id],
                embeddings=[embedding],
                documents=[item.content],
                metadatas=[
                    {
                        "memory_type": item.memory_type,
                        "user_id": item.user_id,
                        "session_id": item.session_id or "",
                        "importance": item.importance,
                        "created_at": item.created_at.isoformat(),
                        **(item.metadata or {}),
                    }
                ],
            )

            # 持久化
            if hasattr(self.client, "persist"):
                self.client.persist()
        else:
            # 内存模式
            self._memories.append(item)

        logger.debug(f"📝 记忆添加 | {item.id} | 类型: {item.memory_type}")
        return item.id

    def search_similar(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[MemoryItem]:
        """
        相似度搜索

        Args:
            query: 查询文本
            user_id: 用户ID (权限隔离)
            top_k: 返回结果数
            memory_type: 可选的类型过滤
            min_importance: 最小重要度过滤

        Returns:
            记忆列表 (按相似度排序)
        """
        # 生成查询向量
        query_embedding = self.embedding_service.encode(query)[0]

        if self.is_available:
            # ChromaDB查询
            where_filter = {"user_id": user_id}
            if memory_type:
                where_filter["memory_type"] = memory_type

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # 多取一些用于筛选
                where=where_filter,
            )

            # 构建MemoryItem列表
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]

                    # 重要度过滤
                    if metadata.get("importance", 1.0) < min_importance:
                        continue

                    memory = MemoryItem(
                        id=memory_id,
                        content=results["documents"][0][i],
                        memory_type=metadata.get("memory_type", "unknown"),
                        user_id=metadata.get("user_id", user_id),
                        session_id=metadata.get("session_id") or None,
                        importance=metadata.get("importance", 1.0),
                        metadata={
                            k: v
                            for k, v in metadata.items()
                            if k
                            not in [
                                "memory_type",
                                "user_id",
                                "session_id",
                                "importance",
                                "created_at",
                            ]
                        },
                        created_at=(
                            datetime.fromisoformat(metadata["created_at"])
                            if "created_at" in metadata
                            else None
                        ),
                    )
                    memories.append(memory)

                    if len(memories) >= top_k:
                        break

            return memories

        else:
            # 内存模式：简单文本匹配
            return self._search_memory_in_memory(query, user_id, top_k, memory_type)

    def _search_memory_in_memory(
        self, query: str, user_id: str, top_k: int, memory_type: Optional[str]
    ) -> List[MemoryItem]:
        """内存模式的搜索"""
        # 过滤用户ID
        user_memories = [m for m in self._memories if m.user_id == user_id]

        # 过滤类型
        if memory_type:
            user_memories = [m for m in user_memories if m.memory_type == memory_type]

        # 简单文本匹配排序
        query_lower = query.lower()
        scored_memories = []

        for memory in user_memories:
            content_lower = memory.content.lower()
            score = 0

            # 完全匹配加分
            if query_lower in content_lower:
                score += 10

            # 单词匹配
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            score += len(query_words & content_words) * 2

            # 重要度加权
            score *= memory.importance

            scored_memories.append((score, memory))

        # 排序返回
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored_memories[:top_k]]

    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            if self.is_available:
                self.collection.delete(ids=[memory_id])
                if hasattr(self.client, "persist"):
                    self.client.persist()
            else:
                self._memories = [m for m in self._memories if m.id != memory_id]

            logger.info(f"🗑️ 记忆删除 | {memory_id}")
            return True
        except Exception as e:
            logger.error(f"🔴 删除记忆失败: {e}")
            return False

    def get_user_memories(
        self, user_id: str, memory_type: Optional[str] = None, limit: int = 100
    ) -> List[MemoryItem]:
        """获取用户的所有记忆"""
        if self.is_available:
            where_filter = {"user_id": user_id}
            if memory_type:
                where_filter["memory_type"] = memory_type

            results = self.collection.get(where=where_filter, limit=limit)

            memories = []
            if results["ids"]:
                for i, memory_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i]
                    memory = MemoryItem(
                        id=memory_id,
                        content=results["documents"][i],
                        memory_type=metadata.get("memory_type", "unknown"),
                        user_id=metadata.get("user_id", user_id),
                        session_id=metadata.get("session_id") or None,
                        importance=metadata.get("importance", 1.0),
                        created_at=(
                            datetime.fromisoformat(metadata["created_at"])
                            if "created_at" in metadata
                            else None
                        ),
                    )
                    memories.append(memory)

            return memories
        else:
            # 内存模式
            memories = [m for m in self._memories if m.user_id == user_id]
            if memory_type:
                memories = [m for m in memories if m.memory_type == memory_type]
            return memories[:limit]

    def update_memory_importance(self, memory_id: str, importance: float):
        """更新记忆重要度"""
        if self.is_available:
            # ChromaDB只支持获取后重新添加
            result = self.collection.get(ids=[memory_id])
            if result["ids"]:
                metadata = result["metadatas"][0]
                metadata["importance"] = importance

                self.collection.update(ids=[memory_id], metadatas=[metadata])

        else:
            # 内存模式
            for m in self._memories:
                if m.id == memory_id:
                    m.importance = importance
                    break

    def cleanup_old_memories(self, days: int = 90):
        """清理过期记忆"""
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 3600)

        if self.is_available:
            # ChromaDB: 获取所有记录并删除旧的
            results = self.collection.get()
            if results["ids"]:
                to_delete = []
                for i, memory_id in enumerate(results["ids"]):
                    created_at = datetime.fromisoformat(
                        results["metadatas"][i].get(
                            "created_at", datetime.utcnow().isoformat()
                        )
                    )
                    if created_at.timestamp() < cutoff:
                        to_delete.append(memory_id)

                if to_delete:
                    self.collection.delete(ids=to_delete)
                    logger.info(f"🧹 清理记忆 | 删除 {len(to_delete)} 条")

        else:
            # 内存模式
            original_count = len(self._memories)
            self._memories = [
                m for m in self._memories if m.created_at.timestamp() >= cutoff
            ]
            deleted = original_count - len(self._memories)
            if deleted:
                logger.info(f"🧹 清理记忆 | 删除 {deleted} 条")

    def get_stats(self) -> Dict:
        """获取存储统计"""
        if self.is_available:
            count = self.collection.count()
        else:
            count = len(self._memories)

        return {
            "total_memories": count,
            "storage_type": "chromadb" if self.is_available else "memory",
            "embedding_model": self.embedding_service.model_name,
            "embedding_available": self.embedding_service.is_available,
        }


# 全局记忆存储实例
vector_memory = VectorMemoryStore()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 向量记忆存储")
    print("=" * 60)

    print("\n【功能】")
    print("  - 语义相似度搜索")
    print("  - 多记忆类型分类")
    print("  - 基于时间的衰减")
    print("  - 重要性排序")

    print("\n【技术栈】")
    print("  - ChromaDB: 向量数据库")
    print("  - SentenceTransformers: 文本嵌入")

    print("\n【使用前检查】")
    print(f"  ChromaDB可用: {CHROMADB_AVAILABLE}")
    print(f"  嵌入模型可用: {EMBEDDINGS_AVAILABLE}")

    print("\n【API】")
    print("  - add_memory(): 添加记忆")
    print("  - search_similar(): 相似度搜索")
    print("  - get_user_memories(): 获取用户记忆")
    print("  - cleanup_old_memories(): 清理过期记忆")

    print("\n" + "=" * 60)

    # 简单测试
    if CHROMADB_AVAILABLE:
        print("\n【运行测试】")

        # 添加测试记忆
        test_memories = [
            MemoryItem(
                id="mem_001",
                content="用户喜欢喝抹茶拿铁，不喜欢太甜",
                memory_type="fact",
                user_id="user_test",
            ),
            MemoryItem(
                id="mem_002",
                content="用户有轻度高血压，正在控制饮食",
                memory_type="health",
                user_id="user_test",
                importance=0.9,
            ),
            MemoryItem(
                id="mem_003",
                content="用户最近睡眠质量不太好",
                memory_type="health",
                user_id="user_test",
                importance=0.8,
            ),
        ]

        for mem in test_memories:
            vector_memory.add_memory(mem)
            print(f"  ✓ 添加记忆: {mem.content[:30]}...")

        # 搜索测试
        print("\n【搜索测试】")
        query = "用户喜欢喝什么？"
        results = vector_memory.search_similar(query, "user_test", top_k=3)
        print(f'  查询: "{query}"')
        print(f"  找到 {len(results)} 条相关记忆:")
        for r in results:
            print(
                f"    - [{r.memory_type}] {r.content[:40]}... (重要度: {r.importance})"
            )

        # 统计
        print(f"\n【存储统计】")
        print(f"  {vector_memory.get_stats()}")

        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
