# Deploy da API Astrológica no Portainer

## 📋 Pré-requisitos

- Portainer instalado e configurado
- Docker Swarm mode ativado
- Acesso ao Portainer via interface web

## 🚀 Passos para Deploy

### 1. Construir a Imagem Docker

```bash
# Na pasta do projeto
docker build -t api-astrologica:latest .
```

### 2. Fazer Push da Imagem (opcional)

Se você tem um registry privado:

```bash
# Tag da imagem
docker tag api-astrologica:latest seu-registry/api-astrologica:latest

# Push para o registry
docker push seu-registry/api-astrologica:latest
```

### 3. Deploy via Portainer

#### Opção A: Via Interface Web

1. Acesse o Portainer
2. Vá em **Stacks** → **Add Stack**
3. Escolha **Web editor**
4. Cole o conteúdo do arquivo `stack.yml`
5. Ajuste as configurações conforme necessário
6. Clique em **Deploy the stack**

#### Opção B: Via Upload de Arquivo

1. Acesse o Portainer
2. Vá em **Stacks** → **Add Stack**
3. Escolha **Upload**
4. Faça upload do arquivo `stack.yml`
5. Clique em **Deploy the stack**

### 4. Configurações Opcionais

#### Traefik (se disponível)

Se você tem Traefik configurado, ajuste as labels no `stack.yml`:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.api-astrologica.rule=Host(`seu-dominio.com`)"
  - "traefik.http.services.api-astrologica.loadbalancer.server.port=8000"
```

#### Recursos

Ajuste os recursos conforme sua infraestrutura:

```yaml
resources:
  limits:
    cpus: '2'        # Ajuste conforme necessário
    memory: 1G       # Ajuste conforme necessário
  reservations:
    cpus: '0.5'
    memory: 512M
```

## 🔧 Configurações de Ambiente

### Variáveis de Ambiente

```env
PYTHONUNBUFFERED=1
PYTHONPATH=/app
```

### Portas

- **8000**: Porta da API (HTTP)

## 🏥 Health Check

A API possui health check configurado em:
- **Endpoint**: `/health`
- **Intervalo**: 30 segundos
- **Timeout**: 10 segundos
- **Retries**: 3 tentativas

## 🔍 Monitoramento

### Logs

Visualize os logs no Portainer:
1. Vá em **Stacks** → **api-astrologica**
2. Clique no serviço
3. Vá na aba **Logs**

### Status

Verifique o status:
- **URL**: `http://localhost:8000/health`
- **Ping**: `http://localhost:8000/ping`

## 🛠️ Troubleshooting

### Erro de Health Check

Se o health check falhar:

1. Verifique se a porta 8000 está disponível
2. Verifique os logs do container
3. Teste manualmente: `curl http://localhost:8000/health`

### Erro de Recursos

Se houver problemas de recursos:

1. Ajuste os limites no `stack.yml`
2. Monitore o uso de CPU/RAM no Portainer
3. Considere scaling horizontal

### Erro de Rede

Se houver problemas de conectividade:

1. Verifique se a rede `api-network` foi criada
2. Teste conectividade entre containers
3. Verifique firewall/iptables

## 📊 Endpoints Disponíveis

- **GET** `/` - Página inicial
- **GET** `/health` - Health check
- **GET** `/ping` - Ping básico
- **POST** `/astro-completo-nasa` - Análise astrológica completa
- **POST** `/planetas-individualizados` - Planetas individualizados
- **POST** `/transito-especifico` - Trânsito específico

## 🔄 Atualização

Para atualizar a API:

1. Construa nova imagem
2. Faça push para o registry
3. No Portainer, vá em **Stacks** → **api-astrologica**
4. Clique em **Editor**
5. Clique em **Update the stack**

## 📝 Notas

- A API é otimizada para análises astrológicas
- Suporta dados de entrada das APIs de astrologia
- Possui otimizações para o limite de tokens do Gemini
- Inclui fallbacks para garantir estabilidade 