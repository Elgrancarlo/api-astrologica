#!/bin/bash

# Script para construir e fazer push da imagem para Docker Hub
# Execute este script localmente

set -e

# Configurações
DOCKER_USERNAME="elgrancarlo"
IMAGE_NAME="api-astrologica"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

echo "🚀 Construindo e fazendo push da API Astrológica..."

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o Docker e tente novamente."
    exit 1
fi

# Construir a imagem
echo "🔨 Construindo imagem Docker..."
if docker build -t $FULL_IMAGE_NAME .; then
    echo "✅ Imagem construída com sucesso!"
else
    echo "❌ Falha ao construir a imagem"
    exit 1
fi

# Verificar se está logado no Docker Hub
echo "🔐 Verificando login no Docker Hub..."
if ! docker info | grep -q "Username:"; then
    echo "⚠️  Você precisa fazer login no Docker Hub:"
    echo "   docker login"
    echo ""
    read -p "Pressione Enter após fazer login..."
fi

# Fazer push da imagem
echo "📤 Fazendo push para Docker Hub..."
if docker push $FULL_IMAGE_NAME; then
    echo "✅ Push realizado com sucesso!"
else
    echo "❌ Falha no push para Docker Hub"
    exit 1
fi

# Testar a imagem localmente
echo "🧪 Testando imagem localmente..."
docker stop api-astrologica-test 2>/dev/null || true
docker rm api-astrologica-test 2>/dev/null || true

if docker run -d --name api-astrologica-test -p 8001:8000 $FULL_IMAGE_NAME; then
    echo "✅ Container de teste iniciado na porta 8001"
    
    # Aguardar alguns segundos
    sleep 5
    
    # Testar health check
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Health check OK!"
    else
        echo "⚠️  Health check falhou, mas a imagem foi criada"
    fi
    
    # Parar container de teste
    docker stop api-astrologica-test > /dev/null 2>&1
    docker rm api-astrologica-test > /dev/null 2>&1
else
    echo "❌ Falha ao testar imagem localmente"
fi

echo ""
echo "🎉 Processo concluído!"
echo "📋 Informações da imagem:"
echo "   - Nome: $FULL_IMAGE_NAME"
echo "   - Disponível em: https://hub.docker.com/r/$DOCKER_USERNAME/$IMAGE_NAME"
echo ""
echo "💡 Próximos passos:"
echo "   1. Faça deploy da stack no Portainer usando o arquivo stack.yml"
echo "   2. A imagem será baixada automaticamente do Docker Hub"
echo "   3. Acesse https://api.astrologia.illumiai.com/health para verificar" 