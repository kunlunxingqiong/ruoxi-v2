"""
🌸 若曦V2 记忆API
管理若曦的长期记忆系统
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.exceptions import ValidationException
from core.log_manager import get_logger

logger = get_logger(__name__)

router = APIRouter()


class MemoryCreate(BaseModel):
    """创建记忆请求"""

    user_id: str = Field(..., description="用户ID")
    memory_type: str = Field(
        ..., description="记忆类型: fact/event/preference/emotion/goal"
    )
    content: str = Field(..., description="记忆内容", min_length=1, max_length=2000)
    summary: Optional[str] = Field(default=None, description="内容摘要")
    importance: float = Field(default=50.0, ge=0, le=100, description="重要程度 0-100")


class MemoryResponse(BaseModel):
    """记忆响应"""

    id: str
    user_id: str
    memory_type: str
    content: str
    summary: str
    importance: float
    created_at: str


class MemoryQuery(BaseModel):
    """记忆查询"""

    memories: List[MemoryResponse]
    total: int
    query: str


# 内存存储（实际应该使用数据库）
memories_db: Dict[str, Dict] = {}
memory_counter = 0


def _generate_memory_id() -> str:
    """生成记忆ID"""
    global memory_counter
    memory_counter += 1
    return f"mem_{memory_counter:06d}"


@router.post("/", response_model=MemoryResponse)
async def create_memory(memory: MemoryCreate):
    """
    创建新记忆

    让若曦记住关于用户的重要信息

    **请求示例:**
    ```json
    {
        "user_id": "user_001",
        "memory_type": "preference",
        "content": "用户喜欢喝绿茶，不喜欢咖啡",
        "summary": "喜欢绿茶",
        "importance": 70
    }
    ```
    """
    global memory_counter

    # 验证记忆类型
    valid_types = ["fact", "event", "preference", "emotion", "goal"]
    if memory.memory_type not in valid_types:
        raise ValidationException(f"无效的记忆类型，必须是: {', '.join(valid_types)}")

    memory_id = _generate_memory_id()

    # 保存记忆
    memories_db[memory_id] = {
        "id": memory_id,
        "user_id": memory.user_id,
        "memory_type": memory.memory_type,
        "content": memory.content,
        "summary": (
            memory.summary or memory.content[:50] + "..."
            if len(memory.content) > 50
            else memory.content
        ),
        "importance": memory.importance,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    logger.info(
        f"💾 记忆创建 | {memory_id} | 类型: {memory.memory_type} | 用户: {memory.user_id}"
    )

    mem = memories_db[memory_id]
    return MemoryResponse(
        id=mem["id"],
        user_id=mem["user_id"],
        memory_type=mem["memory_type"],
        content=mem["content"],
        summary=mem["summary"],
        importance=mem["importance"],
        created_at=mem["created_at"].isoformat(),
    )


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    user_id: str = Query(..., description="用户ID"),
    memory_type: Optional[str] = Query(None, description="筛选记忆类型"),
    min_importance: float = Query(0, ge=0, le=100, description="最低重要程度"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
):
    """
    获取记忆列表

    检索若曦记住的关于用户的信息
    """
    # 筛选用户的记忆
    user_memories = [mem for mem in memories_db.values() if mem["user_id"] == user_id]

    # 按类型筛选
    if memory_type:
        user_memories = [
            mem for mem in user_memories if mem["memory_type"] == memory_type
        ]

    # 按重要程度筛选
    user_memories = [
        mem for mem in user_memories if mem["importance"] >= min_importance
    ]

    # 按重要程度排序（高的在前）
    user_memories.sort(key=lambda x: x["importance"], reverse=True)

    # 限制数量
    user_memories = user_memories[:limit]

    # 转换为响应模型
    return [
        MemoryResponse(
            id=mem["id"],
            user_id=mem["user_id"],
            memory_type=mem["memory_type"],
            content=mem["content"],
            summary=mem["summary"],
            importance=mem["importance"],
            created_at=mem["created_at"].isoformat(),
        )
        for mem in user_memories
    ]


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """获取特定记忆详情"""
    if memory_id not in memories_db:
        raise HTTPException(status_code=404, detail="记忆不存在")

    mem = memories_db[memory_id]
    return MemoryResponse(
        id=mem["id"],
        user_id=mem["user_id"],
        memory_type=mem["memory_type"],
        content=mem["content"],
        summary=mem["summary"],
        importance=mem["importance"],
        created_at=mem["created_at"].isoformat(),
    )


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    if memory_id not in memories_db:
        raise HTTPException(status_code=404, detail="记忆不存在")

    del memories_db[memory_id]
    logger.info(f"🗑️ 记忆删除: {memory_id}")

    return {"success": True, "message": "记忆已删除"}


@router.get("/search/{query}")
async def search_memories(
    query: str,
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    搜索记忆

    简单的关键词匹配搜索
    """
    query_lower = query.lower()

    # 筛选并评分
    matching_memories = []
    for mem in memories_db.values():
        if mem["user_id"] != user_id:
            continue

        # 简单匹配评分
        score = 0
        if query_lower in mem["content"].lower():
            score += 10
        if query_lower in mem["summary"].lower():
            score += 5
        if query_lower in mem["memory_type"].lower():
            score += 3

        if score > 0:
            matching_memories.append(
                {"memory": mem, "score": score + mem["importance"] / 10}
            )

    # 按评分排序
    matching_memories.sort(key=lambda x: x["score"], reverse=True)

    # 限制数量
    matching_memories = matching_memories[:limit]

    return {
        "query": query,
        "total": len(matching_memories),
        "results": [
            {
                "id": item["memory"]["id"],
                "type": item["memory"]["memory_type"],
                "content": item["memory"]["content"],
                "importance": item["memory"]["importance"],
                "score": round(item["score"], 2),
            }
            for item in matching_memories
        ],
    }


@router.get("/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """
    获取用户记忆统计

    显示若曦记住了多少关于用户的信息
    """
    user_memories = [mem for mem in memories_db.values() if mem["user_id"] == user_id]

    # 按类型统计
    type_stats = {}
    for mem in user_memories:
        mem_type = mem["memory_type"]
        if mem_type not in type_stats:
            type_stats[mem_type] = 0
        type_stats[mem_type] += 1

    return {
        "user_id": user_id,
        "total_memories": len(user_memories),
        "by_type": type_stats,
        "high_importance": len([m for m in user_memories if m["importance"] >= 70]),
        "last_updated": (
            max([m["updated_at"].isoformat() for m in user_memories])
            if user_memories
            else None
        ),
    }
