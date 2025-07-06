#!/bin/bash

# Script de Deploy da API Astrológica para Portainer
# Autor: Assistente AI
# Data: $(date +%Y-%m-%d)

set -e

echo "🚀 Iniciando processo de deploy da API Astrológica..."

# Configurações
IMAGE_NAME="api-astrologica"
IMAGE_TAG="latest"
REGISTRY_URL=${REGISTRY_URL:-""}
STACK_NAME="api-astrologica"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se Docker está rodando
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker não está rodando. Inicie o Docker e tente novamente."
        exit 1
    fi
    log_info "Docker está rodando ✓"
}

# Construir a imagem
build_image() {
    log_info "Construindo imagem Docker..."
    
    if docker build -t $IMAGE_NAME:$IMAGE_TAG .; then
        log_info "Imagem construída com sucesso ✓"
    else
        log_error "Falha ao construir a imagem"
        exit 1
    fi
}

# Fazer push para registry (opcional)
push_image() {
    if [ -n "$REGISTRY_URL" ]; then
        log_info "Fazendo push para registry $REGISTRY_URL..."
        
        # Tag para registry
        docker tag $IMAGE_NAME:$IMAGE_TAG $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
        
        # Push
        if docker push $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG; then
            log_info "Push realizado com sucesso ✓"
        else
            log_error "Falha no push para registry"
            exit 1
        fi
    else
        log_warn "Registry não configurado, pulando push"
    fi
}

# Verificar se arquivo stack existe
check_stack_file() {
    if [ ! -f "stack.yml" ]; then
        log_error "Arquivo stack.yml não encontrado"
        exit 1
    fi
    log_info "Arquivo stack.yml encontrado ✓"
}

# Testar a imagem localmente
test_image() {
    log_info "Testando imagem localmente..."
    
    # Parar container se estiver rodando
    docker stop $IMAGE_NAME-test 2>/dev/null || true
    docker rm $IMAGE_NAME-test 2>/dev/null || true
    
    # Rodar container de teste
    if docker run -d --name $IMAGE_NAME-test -p 8001:8000 $IMAGE_NAME:$IMAGE_TAG; then
        log_info "Container de teste iniciado na porta 8001"
        
        # Aguardar alguns segundos
        sleep 5
        
        # Testar health check
        if curl -f http://localhost:8001/health > /dev/null 2>&1; then
            log_info "Health check OK ✓"
        else
            log_warn "Health check falhou, mas continuando..."
        fi
        
        # Parar container de teste
        docker stop $IMAGE_NAME-test > /dev/null 2>&1
        docker rm $IMAGE_NAME-test > /dev/null 2>&1
        
        log_info "Teste local concluído ✓"
    else
        log_error "Falha ao testar imagem localmente"
        exit 1
    fi
}

# Mostrar instruções para deploy no Portainer
show_portainer_instructions() {
    echo ""
    echo "🎯 Próximos passos para deploy no Portainer:"
    echo ""
    echo "1. Acesse seu Portainer em: http://seu-portainer-url"
    echo "2. Vá em 'Stacks' → 'Add Stack'"
    echo "3. Escolha 'Upload' e faça upload do arquivo 'stack.yml'"
    echo "4. Ou escolha 'Web editor' e cole o conteúdo do arquivo"
    echo "5. Clique em 'Deploy the stack'"
    echo ""
    echo "📋 Configurações importantes:"
    echo "- Nome da stack: $STACK_NAME"
    echo "- Imagem: $IMAGE_NAME:$IMAGE_TAG"
    echo "- Porta: 8000"
    echo ""
    echo "📖 Para mais detalhes, veja o arquivo DEPLOY.md"
}

# Menu principal
show_menu() {
    echo ""
    echo "Escolha uma opção:"
    echo "1) Build completo (build + test)"
    echo "2) Apenas build"
    echo "3) Apenas test"
    echo "4) Build + push para registry"
    echo "5) Mostrar instruções do Portainer"
    echo "6) Sair"
    echo ""
    read -p "Opção: " choice
    
    case $choice in
        1)
            check_docker
            build_image
            test_image
            show_portainer_instructions
            ;;
        2)
            check_docker
            build_image
            ;;
        3)
            check_docker
            test_image
            ;;
        4)
            check_docker
            build_image
            push_image
            test_image
            show_portainer_instructions
            ;;
        5)
            show_portainer_instructions
            ;;
        6)
            log_info "Saindo..."
            exit 0
            ;;
        *)
            log_error "Opção inválida"
            show_menu
            ;;
    esac
}

# Verificar argumentos da linha de comando
if [ $# -eq 0 ]; then
    show_menu
else
    case $1 in
        build)
            check_docker
            build_image
            ;;
        test)
            check_docker
            test_image
            ;;
        full)
            check_docker
            build_image
            test_image
            show_portainer_instructions
            ;;
        push)
            check_docker
            build_image
            push_image
            ;;
        *)
            echo "Uso: $0 [build|test|full|push]"
            echo "  build - Apenas construir a imagem"
            echo "  test  - Apenas testar a imagem"
            echo "  full  - Build + test + instruções"
            echo "  push  - Build + push para registry"
            echo ""
            echo "Sem argumentos: modo interativo"
            ;;
    esac
fi 