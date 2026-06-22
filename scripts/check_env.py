#!/usr/bin/env python3
"""
🌸 若曦V2 环境检查脚本
检查运行环境是否满足要求
"""

import importlib
import subprocess
import sys
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PINK = "\033[95m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"


REQUIRED_PACKAGES = {
    "fastapi": "0.100.0",
    "uvicorn": "0.23.0",
    "pydantic": "2.0.0",
    "python-jose": "3.3.0",
    "passlib": "1.7.4",
    "google-generativeai": "0.7.0",
    "groq": "0.9.0",
}

OPTIONAL_PACKAGES = {
    "chromadb": "向量数据库支持",
    "redis": "Redis缓存支持",
    "prometheus-client": "监控指标支持",
}


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"{Colors.BLUE}🐍 Python版本...{Colors.END}", end=" ")

    if version.major >= 3 and version.minor >= 10:
        print(
            f"{Colors.GREEN}✅ {version.major}.{version.minor}.{version.micro}{Colors.END}"
        )
        return True
    else:
        print(
            f"{Colors.RED}❌ {version.major}.{version.minor}.{version.micro} (需要3.10+){Colors.END}"
        )
        return False


def check_package(name, min_version=None):
    """检查包是否安装"""
    try:
        module = importlib.import_module(name.replace("-", "_"))
        version = getattr(module, "__version__", "unknown")
        return True, version
    except ImportError:
        return False, None


def check_dependencies():
    """检查依赖"""
    print(f"\n{Colors.BLUE}📦 核心依赖检查...{Colors.END}")
    all_ok = True

    for package, min_version in REQUIRED_PACKAGES.items():
        installed, version = check_package(package)
        if installed:
            print(f"  {Colors.GREEN}✅{Colors.END} {package}=={version}")
        else:
            print(f"  {Colors.RED}❌{Colors.END} {package} (未安装)")
            all_ok = False

    return all_ok


def check_optional():
    """检查可选依赖"""
    print(f"\n{Colors.BLUE}📦 可选依赖检查...{Colors.END}")

    for package, description in OPTIONAL_PACKAGES.items():
        installed, version = check_package(package)
        if installed:
            print(
                f"  {Colors.GREEN}✅{Colors.END} {package}=={version} - {description}"
            )
        else:
            print(f"  {Colors.YELLOW}⚠️{Colors.END} {package} 未安装 - {description}")


def check_env_file():
    """检查环境变量文件"""
    print(f"\n{Colors.BLUE}⚙️  环境变量...{Colors.END}", end=" ")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print(f"{Colors.GREEN}✅ .env 文件存在{Colors.END}")

        # 检查关键变量
        with open(env_file, "r") as f:
            content = f.read()
            critical_vars = ["RUOXI_JWT_SECRET", "GEMINI_API_KEY"]
            missing = [
                var
                for var in critical_vars
                if var not in content
                or f"{var}=" in content
                or f"{var}=your" in content
            ]

            if missing:
                print(f"  {Colors.YELLOW}⚠️  请配置: {', '.join(missing)}{Colors.END}")
        return True
    elif env_example.exists():
        print(f"{Colors.YELLOW}⚠️  未找到.env，但有.env.example请复制编辑{Colors.END}")
        return False
    else:
        print(f"{Colors.RED}❌ 未找到环境变量文件{Colors.END}")
        return False


def check_directories():
    """检查目录结构"""
    print(f"\n{Colors.BLUE}📁 目录结构...{Colors.END}")

    required_dirs = [
        "core",
        "platform/backend",
        "tests",
        "docs",
        "docker",
    ]

    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  {Colors.GREEN}✅{Colors.END} {dir_path}/")
        else:
            print(f"  {Colors.RED}❌{Colors.END} {dir_path}/ (缺失)")


def check_disk_space():
    """检查磁盘空间"""
    print(f"\n{Colors.BLUE}💾 磁盘空间...{Colors.END}", end=" ")

    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)

        if free_gb >= 1:
            print(f"{Colors.GREEN}✅ 剩余 {free_gb}GB{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ 仅剩余 {free_gb}GB (建议 > 1GB){Colors.END}")
            return False
    except:
        print(f"{Colors.YELLOW}⚠️  无法检查{Colors.END}")
        return True


def check_memory():
    """检查内存"""
    print(f"{Colors.BLUE}🧠 内存...{Colors.END}", end=" ")

    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()

        for line in meminfo.split("\n"):
            if "MemTotal" in line:
                total_kb = int(line.split()[1])
                total_gb = total_kb / (1024 * 1024)

                if total_gb >= 2:
                    print(f"{Colors.GREEN}✅ {total_gb:.1f}GB{Colors.END}")
                    return True
                else:
                    print(
                        f"{Colors.YELLOW}⚠️  {total_gb:.1f}GB (建议 > 2GB){Colors.END}"
                    )
                    return True
    except:
        pass

    print(f"{Colors.YELLOW}⚠️  无法检查{Colors.END}")
    return True


def print_recommendations():
    """打印建议"""
    print(f"\n{Colors.PINK}{'='*50}{Colors.END}")
    print(f"{Colors.PINK}💡 部署建议{Colors.END}")
    print(f"{Colors.PINK}{'='*50}{Colors.END}\n")

    print(f"{Colors.CYAN}1. 安装所有依赖:{Colors.END}")
    print(f"   pip install -r requirements.txt\n")

    print(f"{Colors.CYAN}2. 配置环境变量:{Colors.END}")
    print(f"   cp .env.example .env")
    print(f"   # 编辑 .env 配置API密钥\n")

    print(f"{Colors.CYAN}3. 启动服务:{Colors.END}")
    print(f"   python scripts/quick_start.py\n")

    print(f"{Colors.CYAN}4. 测试API:{Colors.END}")
    print(f"   python scripts/test_api.py\n")


def main():
    print(f"\n{Colors.PINK}{Colors.BOLD}")
    print("  🌸 若曦V2 环境检查 🌸")
    print(f"{Colors.END}\n")

    results = []

    results.append(("Python版本", check_python_version()))
    results.append(("核心依赖", check_dependencies()))
    check_optional()
    results.append(("环境变量", check_env_file()))
    check_directories()
    results.append(("磁盘空间", check_disk_space()))
    results.append(("内存", check_memory()))

    # 汇总
    print(f"\n{Colors.PINK}{'='*50}{Colors.END}")
    print(f"{Colors.PINK}📊 检查结果{Colors.END}")
    print(f"{Colors.PINK}{'='*50}{Colors.END}\n")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}✅" if result else f"{Colors.RED}❌"
        print(f"  {status}{Colors.END} {name}")

    print(f"\n{Colors.BLUE}总计: {passed}/{total} 项通过{Colors.END}")

    if passed == total:
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}🎉 环境检查通过！可以启动若曦了！{Colors.END}"
        )
    else:
        print(f"\n{Colors.YELLOW}⚠️  部分检查未通过，请根据提示修复{Colors.END}")
        print_recommendations()


if __name__ == "__main__":
    main()
