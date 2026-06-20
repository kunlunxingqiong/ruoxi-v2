#!/bin/bash
# 🌸 若曦V2 - 部署脚本
# 支持开发环境和生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║              🌸 若曦V2 部署脚本                              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ========== 帮助信息 ==========
function show_help() {
    echo "使用方法: ./deploy.sh [选项] [环境]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示帮助"
    echo "  -b, --build      仅构建镜像"
    echo "  -u, --up         启动服务"
    echo "  -d, --down       停止服务"
    echo "  -l, --logs       查看日志"
    echo "  -s, --status     查看状态"
    echo "  -c, --clean      清理数据"
    echo ""
    echo "环境:"
    echo "  dev              开发环境 (docker-compose.dev.yml)"
    echo "  prod             生产环境 (docker-compose.yml) [默认]"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh -u dev     # 启动开发环境"
    echo "  ./deploy.sh -b prod    # 构建生产环境镜像"
    echo "  ./deploy.sh -d         # 停止生产环境"
}

# ========== 检查依赖 ==========
function check_dependencies() {
    echo -e "${YELLOW}🔍 检查依赖...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安装${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查通过${NC}"
}

# ========== 构建镜像 ==========
function build_images() {
    local env=$1
    echo -e "${YELLOW}🏗️ 构建镜像 (${env}环境)...${NC}"
    
    cd "$PROJECT_DIR/docker"
    
    if [ "$env" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml pull
    else
        docker-compose -f docker-compose.yml build --no-cache
    fi
    
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# ========== 启动服务 ==========
function start_services() {
    local env=$1
    echo -e "${YELLOW}🚀 启动服务 (${env}环境)...${NC}"
    
    cd "$PROJECT_DIR/docker"
    
    if [ "$env" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml up -d
        echo ""
        echo -e "${GREEN}✅ 开发环境已启动${NC}"
        echo ""
        echo "服务地址:"
        echo "  PostgreSQL: localhost:5433"
        echo "  Redis:      localhost:6380"
        echo "  ChromaDB:   localhost:8002"
        echo "  MinIO:      localhost:9000 (Console: 9001)"
        echo "  MailHog:    localhost:8025"
    else
        # 检查环境变量
        if [ ! -f "$PROJECT_DIR/.env" ]; then
            echo -e "${YELLOW}⚠️ 未找到.env文件，使用默认配置${NC}"
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env" 2>/dev/null || echo "请手动创建.env文件"
        fi
        
        docker-compose -f docker-compose.yml up -d
        echo ""
        echo -e "${GREEN}✅ 生产环境已启动${NC}"
        echo ""
        echo "服务地址:"
        echo "  前端:    http://localhost"
        echo "  后端API: http://localhost:8000"
        echo "  文档:    http://localhost/docs"
    fi
    
    echo ""
    echo -e "${BLUE}查看日志: docker-compose -f docker-compose${env:+.$env}.yml logs -f${NC}"
}

# ========== 停止服务 ==========
function stop_services() {
    local env=$1
    echo -e "${YELLOW}🛑 停止服务 (${env}环境)...${NC}"
    
    cd "$PROJECT_DIR/docker"
    
    if [ "$env" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml down
    else
        docker-compose -f docker-compose.yml down
    fi
    
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# ========== 查看日志 ==========
function view_logs() {
    local env=$1
    local service=$2
    
    cd "$PROJECT_DIR/docker"
    
    if [ "$env" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml logs -f "$service"
    else
        docker-compose -f docker-compose.yml logs -f "$service"
    fi
}

# ========== 查看状态 ==========
function show_status() {
    local env=$1
    
    cd "$PROJECT_DIR/docker"
    
    if [ "$env" == "dev" ]; then
        docker-compose -f docker-compose.dev.yml ps
    else
        docker-compose -f docker-compose.yml ps
    fi
}

# ========== 清理数据 ==========
function clean_data() {
    local env=$1
    
    echo -e "${RED}⚠️ 警告: 这将删除所有数据!${NC}"
    read -p "确认清理? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_DIR/docker"
        
        if [ "$env" == "dev" ]; then
            docker-compose -f docker-compose.dev.yml down -v
        else
            docker-compose -f docker-compose.yml down -v
        fi
        
        echo -e "${GREEN}✅ 数据已清理${NC}"
    else
        echo "已取消"
    fi
}

# ========== 主逻辑 ==========
ACTION=""
ENV="prod"
SERVICE=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--build)
            ACTION="build"
            shift
            ;;
        -u|--up)
            ACTION="up"
            shift
            ;;
        -d|--down)
            ACTION="down"
            shift
            ;;
        -l|--logs)
            ACTION="logs"
            shift
            ;;
        -s|--status)
            ACTION="status"
            shift
            ;;
        -c|--clean)
            ACTION="clean"
            shift
            ;;
        dev)
            ENV="dev"
            shift
            ;;
        prod)
            ENV="prod"
            shift
            ;;
        *)
            SERVICE=$1
            shift
            ;;
    esac
done

# 检查依赖
check_dependencies

# 执行动作
case $ACTION in
    build)
        build_images "$ENV"
        ;;
    up)
        start_services "$ENV"
        ;;
    down)
        stop_services "$ENV"
        ;;
    logs)
        view_logs "$ENV" "$SERVICE"
        ;;
    status)
        show_status "$ENV"
        ;;
    clean)
        clean_data "$ENV"
        ;;
    *)
        show_help
        exit 1
        ;;
esac
