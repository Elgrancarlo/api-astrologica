# 🚀 Instruções de Deploy - API Astrológica

## 📋 Processo Completo

### **1. Construir e Enviar para Docker Hub (AQUI)**
```bash
# 1. Fazer login no Docker Hub
docker login

# 2. Executar o script de build
./build-and-push.sh
```

### **2. Deploy no Portainer (LÁ)**
1. Acesse seu Portainer
2. Vá em **Stacks** → **Add Stack**
3. Nome da stack: `api-astrologica`
4. Escolha **Web editor**
5. Cole o conteúdo do arquivo `stack.yml`
6. Clique em **Deploy the stack**

### **3. Verificar Funcionamento**
- Acesse: `https://api.astrologia.illumiai.com/health`
- Deve retornar: `{"status": "healthy"}`

## 🔧 Detalhes Técnicos

### **Imagem Docker**
- **Nome**: `elgrancarlo/api-astrologica:latest`
- **Registry**: Docker Hub
- **Público**: Sim (pode ser baixado automaticamente)

### **Network**
- **Nome**: `network_public`
- **Tipo**: Externa (deve existir no Portainer)
- **Traefik**: Configurado para HTTPS

### **Domínio**
- **URL**: `api.astrologia.illumiai.com`
- **SSL**: Let's Encrypt automático
- **Porta**: 8000 (interna)

## 🛠️ Troubleshooting

### **Se o build falhar:**
```bash
# Verificar Docker
docker --version

# Verificar se está logado
docker info | grep Username
```

### **Se o deploy falhar:**
1. Verificar se `network_public` existe no Portainer
2. Verificar se Traefik está configurado
3. Verificar se DNS aponta para o servidor

### **Se a API não responder:**
1. Verificar logs no Portainer
2. Testar localmente: `http://localhost:8000/health`
3. Verificar se a porta 8000 está livre

## 🎯 Resumo

**AQUI (Local):**
- ✅ Build da imagem
- ✅ Push para Docker Hub

**LÁ (Portainer):**
- ✅ Deploy da stack
- ✅ Traefik configura SSL
- ✅ API fica disponível

**Resultado:**
- 🌐 `https://api.astrologia.illumiai.com/health` 