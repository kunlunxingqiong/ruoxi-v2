#!/usr/bin/env python3
"""
🌸 若曦V2 快速启动脚本
一键启动后端服务
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

# 颜色输出
class Colors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """打印启动横幅"""
    print(f"""
{Colors.PINK}{Colors.BOLD}
    🌸 若曦V2 快速启动脚本 🌸
{Colors.END}
    你的AI医生朋友 · 温柔陪伴每一天
    """)

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"{Colors.RED}❌ 需要Python 3.10+，当前 {version.major}.{version.minor}{Colors.END}")
        return False
    print(f"{Colors.GREEN}✅ Python版本: {version.major}.{version.minor}.{version.micro}{Colors.END}")
    return True

def install_dependencies():
    """安装依赖"""
    print(f"\n{Colors.BLUE}📦 安装依赖...{Colors.END}")
    req_file = Path(__file__).parent.parent / "requirements.txt"
    
    if not req_file.exists():
        print(f"{Colors.RED}❌ 未找到requirements.txt{Colors.END}")
        return False
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ 依赖安装完成{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}❌ 依赖安装失败{Colors.END}")
        print(result.stderr)
        return False

def check_env_file():
    """检查环境变量文件"""
    env_file = Path(__file__).parent.parent / ".env"
    env_example = Path(__file__).parent.parent / ".env.example"
    
    if env_file.exists():
        print(f"{Colors.GREEN}✅ 环境变量文件已存在{Colors.END}")
        return True
    
    if env_example.exists():
        print(f"{Colors.YELLOW}⚠️  未找到.env文件，从示例创建...{Colors.END}")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print(f"{Colors.YELLOW}⚠️  请编辑.env文件配置你的API密钥{Colors.END}")
        return True
    
    print(f"{Colors.RED}❌ 未找到.env或.env.example{Colors.END}")
    return False

def start_backend(port=8000, reload=True):
    """启动后端服务"""
    print(f"\n{Colors.PINK}{Colors.BOLD}🚀 启动若曦服务...{Colors.END}")
    print(f"{Colors.BLUE}   端口: {port}{Colors.END}")
    print(f"{Colors.BLUE}   热重载: {'开启' if reload else '关闭'}{Colors.END}")
    print(f"{Colors.BLUE}   API文档: http://localhost:{port}/docs{Colors.END}")
    print(f"{Colors.BLUE}   健康检查: http://localhost:{port}/health{Colors.END}")
    print()
    
    backend_path = Path(__file__).parent.parent / "platform" / "backend"
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
    ]
    
    if reload:
        cmd.extend(["--reload", "--reload-dir", str(backend_path)])
    
    try:
        subprocess.run(cmd, cwd=str(backend_path))
    except KeyboardInterrupt:
        print(f"\n{Colors.PINK}👋 曦曦休息一下，再见~{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description='若曦V2 快速启动')
    parser.add_argument('--port', type=int, default=8000, help='服务端口号')
    parser.add_argument('--no-reload', action='store_true', help='关闭热重载')
    parser.add_argument('--install', action='store_true', help='仅安装依赖')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    if args.install:
        print(f"{Colors.GREEN}✅ 依赖安装完成，退出{Colors.END}")
        sys.exit(0)
    
    # 检查环境变量
    if not check_env_file():
        sys.exit(1)
    
    # 启动服务
    start_backend(args.port, not args.no_reload)

if __name__ == "__main__":
    main()
