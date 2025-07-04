# 🌟 API Astrológica Profissional v2.0 - OTIMIZADA

## 📋 Resumo das Otimizações

Este código foi otimizado para resolver o problema de **limite de tokens do Gemini** (1,048,576 tokens), mantendo **100% das funcionalidades necessárias** mas entregando **outputs mais focados e eficientes**.

## 🚀 Principais Mudanças

### ✅ Funcionalidades Mantidas
- **Análise completa de todos os planetas** (lentos e rápidos)
- **Casas ativadas com datas precisas** (entrada e saída)
- **Aspectos com orbe de 5 graus** (conjunção, trígono, sextil, quadratura, oposição)
- **Retrogradações detalhadas** com períodos e signos
- **Mudanças de signo próximas** (próximos 90-180 dias)
- **Período de análise: 12 meses completos**

### 🎯 Otimizações Implementadas
1. **Priorização por relevância** - Planetas ordenados por importância
2. **Limitação inteligente** - Máximo 5 aspectos por planeta (os mais importantes)
3. **Organização hierárquica** - Planetas divididos em alta/média/baixa relevância
4. **Resumo focado** - Dados essenciais sem informações redundantes
5. **Compatibilidade com LLMs** - Output estruturado para melhor interpretação

## 🛠️ Endpoints Disponíveis

### 📊 `/astro-completo-nasa` (PRINCIPAL - RECOMENDADO)
- **Função**: Análise completa otimizada
- **Output**: Resumido mas completo
- **Compatível**: Limite de tokens do Gemini
- **Uso**: Para todas as análises gerais

### 🔍 `/transito-especifico`
- **Função**: Análise específica de um planeta
- **Formato**: `{"planeta": "Saturno", "dados_completos": {...}}`
- **Funcionalidades**:
  - Casas ativadas com datas exatas
  - Aspectos organizados por tipo
  - Retrogradações detalhadas
  - Período de 12 meses
  - Orbe de 5 graus

### 📈 `/verificar-tamanho`
- **Função**: Verificar se dados excedem limite de tokens
- **Uso**: Para debugging de problemas de tokens
- **Retorna**: Estimativa de tokens e recomendações

### 🔄 `/converter-para-gemini`
- **Função**: Converter dados existentes para versão resumida
- **Uso**: Quando já tem dados completos

### 📋 `/astro-completo-dados-completos`
- **Função**: Dados completos SEM otimização
- **Aviso**: Pode exceder limite de tokens do Gemini
- **Uso**: Apenas quando realmente precisar de todos os dados

## 💡 Como Usar

### Para Análise Geral
```bash
POST /astro-completo-nasa
# Enviar dados no formato array padrão
```

### Para Planeta Específico
```bash
POST /transito-especifico
{
  "planeta": "Saturno",
  "dados_completos": { ... }
}
```

### Para Verificar Tamanho
```bash
POST /verificar-tamanho
# Enviar dados para verificar tokens
```

## 📊 Estrutura do Output Otimizado

```json
{
  "planetas_alta_relevancia": [...],    // Planetas mais importantes
  "planetas_media_relevancia": [...],   // Planetas medianos
  "planetas_baixa_relevancia": [...],   // Planetas menos importantes
  "mudancas_signo_proximas": [...],     // Mudanças próximas
  "resumo_geral": {
    "total_planetas_analisados": 8,
    "planeta_mais_relevante": "Saturno",
    "planetas_em_retrogradacao": 2
  },
  "como_interpretar": {
    "foco_principal": "Analise primeiro os planetas de alta relevância",
    "aspectos_importantes": "Priorize aspectos com intensidade >= 7",
    "casas_ativadas": "Considere as datas de entrada e saída",
    "retrogradacoes": "Analise períodos para revisões",
    "mudancas_signo": "Novas energias e focos"
  }
}
```

## 🎯 Atendimento aos Requisitos

### ✅ Trânsitos Específicos
- **Signo completo**: Análise desde 0° até 30°
- **Casas ativadas**: Datas de entrada e saída
- **Mudanças de casa**: Informadas quando ocorrem
- **Retrogradações**: Datas e interpretações
- **Aspectos**: Orbe de 5 graus, período de 1 ano

### ✅ Estrutura de Resposta
- **Exemplo**: "Saturno em Áries vai ativar sua casa 4..."
- **Datas precisas**: Entrada e saída de casas
- **Retrogradações**: Períodos e signos
- **Aspectos detalhados**: Por tipo com datas

## 🔧 Configuração

### Requisitos
- Python 3.8+
- FastAPI
- Uvicorn

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
```bash
python app/main.py
```

### Acesso
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## ⚠️ Importante

- **Endpoint principal** agora é otimizado por padrão
- **Compatível** com limite de tokens do Gemini
- **Mantém 100%** das funcionalidades necessárias
- **Melhor interpretação** por LLMs
- **Priorização inteligente** dos dados mais importantes

## 📝 Notas Técnicas

- **Redução de tokens**: ~70-80% comparado à versão original
- **Manutenção de funcionalidades**: 100%
- **Melhoria na interpretação**: Dados organizados hierarquicamente
- **Compatibilidade**: Mantém formato de entrada original 