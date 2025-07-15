# 🌟 Novos Endpoints Otimizados para Trânsitos Específicos

## ✅ Problema Resolvido

**ANTES**: Output gigantesco (500KB+) que estourava o contexto do Claude
**DEPOIS**: Output 90% menor mantendo dados essenciais
**RESULTADO**: LLM produz respostas corretas sobre trânsitos específicos

## 🎯 Principais Endpoints

### 1. `/transitos-minimo` (RECOMENDADO)
- **Método**: POST
- **Uso**: Análise geral com output mínimo
- **Redução**: ~90% menor que output completo
- **Ideal para**: Respostas sobre trânsitos seguindo padrão VI

**Exemplo de uso**:
```json
POST /transitos-minimo
[
  // Array com 23+ elementos dos dados astrológicos
]
```

### 2. `/planeta-especifico-minimo`
- **Método**: POST
- **Uso**: Análise de apenas 1 planeta específico
- **Ideal para**: Perguntas como "Como Saturno vai me impactar?"

**Exemplo de uso**:
```json
POST /planeta-especifico-minimo
{
  "planeta": "Saturno",
  "dados_entrada": [
    // Array com 23+ elementos dos dados astrológicos
  ]
}
```

## 📊 Dados Mantidos nos Endpoints Mínimos

- ✅ Casas ativadas com datas precisas
- ✅ Retrogradações com períodos e signo anterior
- ✅ Aspectos maiores (conjunção, trígono, sextil, quadratura, oposição)
- ✅ Orbe de 5 graus para aspectos
- ✅ Período de análise: 12 meses
- ✅ Tempo restante no signo atual
- ✅ Dados para resposta padrão VI. TRÂNSITOS ESPECÍFICOS

## 🔍 Filtros Aplicados

### Endpoint `/transitos-minimo`:
- Planetas com relevância ≥ 5 apenas
- Máximo 3 casas por planeta
- Máximo 5 aspectos por planeta (intensidade ≥ 6)
- Máximo 2 retrogradações por planeta
- Máximo 6 planetas no total
- Máximo 3 mudanças de signo próximas

### Endpoint `/planeta-especifico-minimo`:
- Todos os dados do planeta solicitado
- Apenas aspectos maiores (orbe 5°)
- Todas as casas ativadas encontradas
- Todas as retrogradações do planeta

## 📏 Comparação de Tamanhos

| Endpoint | Tamanho Típico | Tokens Est. | Uso |
|----------|---------------|-------------|-----|
| `/transitos-minimo` | 5-15 KB | 1K-4K | ✅ RECOMENDADO |
| `/planeta-especifico-minimo` | 2-8 KB | 500-2K | ✅ Para planetas específicos |
| `/astro-completo-nasa` | 50-200 KB | 12K-50K | ⚠️ Pode ser grande |
| `/astro-completo-dados-completos` | 200-500+ KB | 50K-125K+ | ❌ Evitar com Claude |

## 🚀 Como Usar

### 1. Para análise geral (RECOMENDADO):
```bash
curl -X POST "http://localhost:8000/transitos-minimo" \
  -H "Content-Type: application/json" \
  -d '[/* seus dados astrológicos */]'
```

### 2. Para planeta específico:
```bash
curl -X POST "http://localhost:8000/planeta-especifico-minimo" \
  -H "Content-Type: application/json" \
  -d '{
    "planeta": "Saturno",
    "dados_entrada": [/* seus dados astrológicos */]
  }'
```

## 📋 Exemplo de Output

### `/transitos-minimo`:
```json
{
  "planetas": [
    {
      "info": {
        "planeta": "Saturno",
        "signo": "Peixes",
        "grau": 15.5,
        "retrogrado": false
      },
      "casas": [
        {
          "casa": 2,
          "entrada": "2025-01-01",
          "saida": "2025-03-01",
          "meses": 2.0
        }
      ],
      "aspectos": [
        {
          "tipo": "conjunção",
          "planeta_natal": "Sol",
          "casa_natal": 1,
          "inicio": "2025-01-01",
          "fim": "2025-01-15",
          "intensidade": 8
        }
      ],
      "retrogradacoes": [
        {
          "inicio": "2025-05-24",
          "fim": "2025-10-15",
          "signo_anterior": "Peixes",
          "dias": 144
        }
      ],
      "tempo_restante": {
        "dias": 120,
        "data_mudanca": "2025-05-15",
        "proximo_signo": "Áries"
      }
    }
  ],
  "mudancas_signo": [
    {
      "planeta": "Saturno",
      "signo_atual": "Peixes",
      "proximo_signo": "Áries",
      "data_mudanca": "2025-05-15"
    }
  ],
  "periodo": "12 meses",
  "data_analise": "2025-01-15",
  "total_planetas_analisados": 2,
  "meta": {
    "tipo": "transitos_minimo",
    "tempo_ms": 150,
    "reducao_tamanho": "~90% menor que output completo",
    "ideal_para": "Respostas sobre trânsitos específicos - padrão VI"
  }
}
```

## 🎯 Vantagens

1. **✅ Não estoura contexto do Claude**: Output 90% menor
2. **✅ LLM produz respostas mais precisas**: Dados focados nos essenciais
3. **✅ Mantém todos dados essenciais**: Nada importante é perdido
4. **✅ Ideal para padrão VI**: Específico para análise de trânsitos
5. **✅ Resposta mais rápida**: Menos dados para processar

## 📈 Recomendações

- **Para análise geral**: Use `/transitos-minimo` 
- **Para planeta específico**: Use `/planeta-especifico-minimo`
- **Para desenvolvimento/debug**: Use `/verificar-tamanho` antes
- **Para casos especiais**: Use `/planetas-individualizados`

## 🔄 Migração

Se você estava usando `/astro-completo-nasa` e tendo problemas de contexto:

1. **Substitua por**: `/transitos-minimo`
2. **Mesmo formato de entrada**: Array com 23+ elementos
3. **Output otimizado**: 90% menor, dados essenciais mantidos
4. **Compatibilidade**: Totalmente compatível com análises de trânsitos

---

🌟 **Agora você pode usar a API sem se preocupar com limites de contexto!** 