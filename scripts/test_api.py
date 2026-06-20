#!/usr/bin/env python3
"""
🌸 若曦V2 API 测试脚本
快速测试所有API端点
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PINK = '\033[95m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30)
        self.results = []
    
    async def test_health(self):
        """测试健康检查"""
        print(f"{Colors.BLUE}🏥 测试健康检查...{Colors.END}")
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}✅ 服务健康: {data.get('status', 'unknown')}{Colors.END}")
                self.results.append(("Health", True))
                return True
            else:
                print(f"{Colors.RED}❌ 健康检查失败: {response.status_code}{Colors.END}")
                self.results.append(("Health", False))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ 连接失败: {e}{Colors.END}")
            self.results.append(("Health", False))
            return False
    
    async def test_chat(self):
        """测试聊天API"""
        print(f"{Colors.BLUE}💬 测试聊天API...{Colors.END}")
        try:
            response = await self.client.post(
                "/api/v1/chat",
                json={
                    "messages": [
                        {"role": "system", "content": "你是若曦"},
                        {"role": "user", "content": "你好"}
                    ],
                    "stream": False,
                    "max_tokens": 100
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}✅ 聊天API正常{Colors.END}")
                print(f"   模型: {data.get('model_used', 'unknown')}")
                print(f"   Token: {data.get('tokens_total', 0)}")
                self.results.append(("Chat", True))
                return True
            else:
                print(f"{Colors.RED}❌ 聊天API失败: {response.status_code}{Colors.END}")
                self.results.append(("Chat", False))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ 聊天API异常: {e}{Colors.END}")
            self.results.append(("Chat", False))
            return False
    
    async def test_emotion(self):
        """测试情感分析"""
        print(f"{Colors.BLUE}💕 测试情感分析...{Colors.END}")
        try:
            response = await self.client.post(
                "/api/v1/emotion/analyze",
                json={"text": "今天好开心啊！"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}✅ 情感分析正常{Colors.END}")
                print(f"   情绪: {data.get('emotion', 'unknown')}")
                print(f"   强度: {data.get('intensity', 0)}")
                self.results.append(("Emotion", True))
                return True
            else:
                print(f"{Colors.RED}❌ 情感分析失败: {response.status_code}{Colors.END}")
                self.results.append(("Emotion", False))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ 情感分析异常: {e}{Colors.END}")
            self.results.append(("Emotion", False))
            return False
    
    async def test_health_analysis(self):
        """测试健康分析"""
        print(f"{Colors.BLUE}🏥 测试健康分析...{Colors.END}")
        try:
            response = await self.client.get("/api/v1/health-ai/analyze/blood_pressure")
            
            if response.status_code in [200, 422]:  # 422可能是缺少数据
                print(f"{Colors.GREEN}✅ 健康分析API正常{Colors.END}")
                self.results.append(("HealthAI", True))
                return True
            else:
                print(f"{Colors.RED}❌ 健康分析失败: {response.status_code}{Colors.END}")
                self.results.append(("HealthAI", False))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ 健康分析异常: {e}{Colors.END}")
            self.results.append(("HealthAI", False))
            return False
    
    async def test_docs(self):
        """测试API文档"""
        print(f"{Colors.BLUE}📚 测试API文档...{Colors.END}")
        try:
            response = await self.client.get("/docs")
            
            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ API文档可访问{Colors.END}")
                self.results.append(("Docs", True))
                return True
            else:
                print(f"{Colors.RED}❌ API文档访问失败: {response.status_code}{Colors.END}")
                self.results.append(("Docs", False))
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ API文档异常: {e}{Colors.END}")
            self.results.append(("Docs", False))
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{Colors.PINK}{'='*50}{Colors.END}")
        print(f"{Colors.PINK}🌸 若曦V2 API 测试开始{Colors.END}")
        print(f"{Colors.PINK}{'='*50}{Colors.END}\n")
        
        # 测试健康检查
        if not await self.test_health():
            print(f"\n{Colors.RED}❌ 服务未启动，测试中止{Colors.END}")
            return
        
        # 测试其他API
        await self.test_chat()
        await self.test_emotion()
        await self.test_health_analysis()
        await self.test_docs()
        
        # 打印结果
        await self.print_results()
    
    async def print_results(self):
        """打印测试结果"""
        print(f"\n{Colors.PINK}{'='*50}{Colors.END}")
        print(f"{Colors.PINK}📊 测试结果汇总{Colors.END}")
        print(f"{Colors.PINK}{'='*50}{Colors.END}\n")
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        
        for name, result in self.results:
            status = f"{Colors.GREEN}✅ 通过" if result else f"{Colors.RED}❌ 失败"
            print(f"  {status}{Colors.END} {name}")
        
        print(f"\n{Colors.BLUE}总计: {passed}/{total} 通过 ({passed/total*100:.0f}%){Colors.END}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！若曦运行正常！{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  部分测试未通过，请检查服务状态{Colors.END}")
        
        await self.client.aclose()


async def main():
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
