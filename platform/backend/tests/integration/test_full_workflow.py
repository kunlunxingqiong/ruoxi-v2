"""若曦V2 端到端整合测试套件"""
import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta


class TestFullWorkflow:
    """完整工作流测试"""
    
    @pytest.mark.asyncio
    async def test_chat_full_lifecycle(self):
        """测试聊天完整生命周期"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # 1. 用户登录
            login_resp = await client.post("/api/auth/login", json={
                "username": "test_user",
                "password": "test_password"
            })
            assert login_resp.status_code == 200
            token = login_resp.json()["access_token"]
            
            # 2. 创建会话
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post("/api/sessions", headers=headers)
            assert session_resp.status_code == 201
            session_id = session_resp.json()["session_id"]
            
            # 3. 发送消息
            chat_resp = await client.post(
                f"/api/sessions/{session_id}/messages",
                headers=headers,
                json={"content": "今天过得怎么样？"}
            )
            assert chat_resp.status_code == 200
            response_data = chat_resp.json()
            assert "response" in response_data
            assert "emotion_state" in response_data
            
            # 4. 获取历史
            history_resp = await client.get(
                f"/api/sessions/{session_id}/messages",
                headers=headers
            )
            assert history_resp.status_code == 200
            messages = history_resp.json()
            assert len(messages) >= 2  # 用户消息 + 若曦回复
            
            # 5. 关闭会话
            close_resp = await client.delete(
                f"/api/sessions/{session_id}",
                headers=headers
            )
            assert close_resp.status_code == 200
    
    @pytest.mark.asyncio
    async def test_websocket_realtime(self):
        """测试WebSocket实时通信"""
        import websockets
        
        uri = "ws://localhost:8000/ws/chat/test_session"
        async with websockets.connect(uri) as websocket:
            # 发送消息
            await websocket.send(json.dumps({
                "type": "message",
                "content": "在吗？",
                "timestamp": datetime.now().isoformat()
            }))
            
            # 接收响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            assert "response" in data
            assert "typing_delay" in data
            assert data["typing_delay"] > 0  # 验证延迟链生效
    
    @pytest.mark.asyncio
    async def test_biological_state_persistence(self):
        """测试生物状态持久化"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # 获取初始状态
            state1 = await client.get("/api/state/biological")
            assert state1.status_code == 200
            
            # 模拟时间推移
            await asyncio.sleep(2)
            
            # 再次获取状态，验证更新
            state2 = await client.get("/api/state/biological")
            assert state2.status_code == 200
            
            # 激素水平应随时间变化
            hormones1 = state1.json()["hormones"]
            hormones2 = state2.json()["hormones"]
            assert hormones1 != hormones2  # 生物节律在流动
    
    def test_memory_recall_integration(self):
        """测试记忆召回集成"""
        from core.memory_graph import get_memory_store
        
        store = get_memory_store()
        
        # 添加测试记忆
        store.add_memory(
            user_id="test_user",
            content="用户喜欢喝乌龙茶",
            emotion_tag="positive",
            importance=0.8
        )
        
        # 查询相关记忆
        memories = store.recall_memories(
            user_id="test_user",
            query="饮料",
            limit=5
        )
        
        assert len(memories) > 0
        assert any("乌龙茶" in str(m) for m in memories)
    
    @pytest.mark.asyncio
    async def test_blush_system_integration(self):
        """测试脸红系统集成"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # 触发脸红场景
            resp = await client.post("/api/interaction/gaze", json={
                "user_id": "test_user",
                "gaze_duration": 3.0,  # 注视3秒
                "eye_contact": True
            })
            assert resp.status_code == 200
            
            state = resp.json()
            assert "blush_level" in state
            assert state["blush_level"] > 0  # 被看着会脸红
            assert "ear_tips" in state["body_reaction"]


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_response_time_under_100ms(self):
        """测试响应时间<100ms"""
        import time
        
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            start = time.time()
            resp = await client.post("/api/chat", json={
                "message": "你好"
            })
            elapsed = (time.time() - start) * 1000  # 转毫秒
            
            assert resp.status_code == 200
            assert elapsed < 100, f"响应时间 {elapsed}ms 超过100ms目标"
    
    @pytest.mark.asyncio
    async def test_concurrent_users(self):
        """测试并发用户处理"""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            tasks = []
            for i in range(10):  # 10个并发用户
                task = client.post("/api/chat", json={
                    "message": f"消息{i}"
                })
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            assert success_count >= 9  # 至少90%成功率


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
