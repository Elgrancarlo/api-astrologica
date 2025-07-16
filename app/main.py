from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import ephem
import math
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Trânsitos Específicos", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELOS ============

class PlanetaInput(BaseModel):
    name: str
    fullDegree: float
    normDegree: float
    speed: float
    isRetro: str
    sign: str
    house: int

class CasaInput(BaseModel):
    house: int
    sign: str
    degree: float

class CasasInput(BaseModel):
    houses: List[CasaInput]

class TransitoEspecificoResponse(BaseModel):
    planeta: str
    signo_atual: str
    grau_atual: float
    casas_ativadas: List[Dict[str, Any]]
    retrogradacoes: List[Dict[str, Any]]
    aspectos_natais: List[Dict[str, Any]]
    periodo_analise: str

# ============ CLASSE PRINCIPAL ============
class TransitoCalculator:
    def __init__(self):
        self.signos = [
            'Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
            'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes'
        ]
        
        self.aspectos_maiores = [
            (0, "conjunção", 5),
            (60, "sextil", 5),
            (90, "quadratura", 5),
            (120, "trígono", 5),
            (180, "oposição", 5)
        ]
        
        # Mapeamento PyEphem
        self.ephem_map = {
            'Sol': ephem.Sun(),
            'Lua': ephem.Moon(),
            'Mercúrio': ephem.Mercury(),
            'Vênus': ephem.Venus(),
            'Marte': ephem.Mars(),
            'Júpiter': ephem.Jupiter(),
            'Saturno': ephem.Saturn(),
            'Urano': ephem.Uranus(),
            'Netuno': ephem.Neptune(),
            'Plutão': ephem.Pluto()
        }
    
    def calcular_posicao_real(self, planeta_nome: str, data: datetime) -> Dict[str, Any]:
        """Calcula posição real usando PyEphem"""
        try:
            planeta = self.ephem_map.get(planeta_nome)
            if not planeta:
                raise ValueError(f"Planeta {planeta_nome} não encontrado")
            
            observer = ephem.Observer()
            observer.date = data.strftime('%Y/%m/%d')
            planeta.compute(observer)
            
            longitude_rad = planeta.hlong
            longitude_graus = float(longitude_rad) * 180 / math.pi
            
            # Calcular velocidade (posição hoje vs amanhã)
            observer.date = (data + timedelta(days=1)).strftime('%Y/%m/%d')
            planeta.compute(observer)
            longitude_amanha = float(planeta.hlong) * 180 / math.pi
            
            velocidade = longitude_amanha - longitude_graus
            if velocidade > 180:
                velocidade -= 360
            elif velocidade < -180:
                velocidade += 360
            
            # Determinar signo e grau no signo
            signo_index = int(longitude_graus // 30)
            grau_no_signo = longitude_graus % 30
            
            return {
                'longitude': longitude_graus,
                'signo': self.signos[signo_index],
                'grau_no_signo': grau_no_signo,
                'velocidade': velocidade,
                'retrogrado': velocidade < 0
            }
        except Exception as e:
            logger.error(f"Erro ao calcular posição real: {e}")
            return None
    
    def calcular_mudancas_casa(self, planeta_nome: str, signo_atual: str, casas: List[CasaInput]) -> List[Dict[str, Any]]:
        """Calcula mudanças de casa dentro do signo atual (máximo 3 casas)"""
        try:
            # Encontrar índice do signo
            signo_index = self.signos.index(signo_atual)
            grau_inicio_signo = signo_index * 30
            grau_fim_signo = grau_inicio_signo + 30
            
            casas_ativadas = []
            hoje = datetime.now()
            
            # Obter posição atual real
            pos_atual = self.calcular_posicao_real(planeta_nome, hoje)
            if not pos_atual:
                return []
            
            # Calcular casas dentro do signo (verificar apenas 3 pontos-chave)
            pontos_chave = [grau_inicio_signo + 5, grau_inicio_signo + 15, grau_inicio_signo + 25]
            
            for grau in pontos_chave:
                casa_info = self.determinar_casa(grau, casas)
                if casa_info:
                    # Calcular quando planeta estará neste grau
                    diff_graus = grau - pos_atual['longitude']
                    if diff_graus < 0:
                        continue  # Já passou
                    
                    dias_ate_grau = diff_graus / abs(pos_atual['velocidade']) if pos_atual['velocidade'] != 0 else 0
                    data_ativacao = hoje + timedelta(days=dias_ate_grau)
                    
                    # Verificar se não já temos esta casa
                    if not any(c['casa'] == casa_info['casa'] for c in casas_ativadas):
                        casas_ativadas.append({
                            'casa': casa_info['casa'],
                            'data_entrada': data_ativacao.strftime('%Y-%m-%d')
                        })
            
            # LIMITAR a máximo 3 casas
            return casas_ativadas[:3]
            
        except Exception as e:
            logger.error(f"Erro ao calcular mudanças de casa: {e}")
            return []
    
    def determinar_casa(self, grau: float, casas: List[CasaInput]) -> Optional[Dict[str, Any]]:
        """Determina casa baseada no grau"""
        casas_ordenadas = sorted(casas, key=lambda x: x.degree)
        
        for i in range(len(casas_ordenadas)):
            cuspide_atual = casas_ordenadas[i]
            proxima_cuspide = casas_ordenadas[(i + 1) % len(casas_ordenadas)]
            
            if proxima_cuspide.degree > cuspide_atual.degree:
                if cuspide_atual.degree <= grau < proxima_cuspide.degree:
                    return {'casa': cuspide_atual.house}
            else:
                if grau >= cuspide_atual.degree or grau < proxima_cuspide.degree:
                    return {'casa': cuspide_atual.house}
        
        return None
    
    def calcular_retrogradacoes_reais(self, planeta_nome: str) -> List[Dict[str, Any]]:
        """Calcula apenas a próxima retrogradação mais relevante"""
        try:
            retrogradacoes = []
            hoje = datetime.now()
            data_fim = hoje + timedelta(days=365)
            
            data_atual = hoje
            em_retrogradacao = False
            inicio_retro = None
            
            while data_atual <= data_fim and len(retrogradacoes) < 1:  # Apenas 1 retrogradação
                pos = self.calcular_posicao_real(planeta_nome, data_atual)
                if not pos:
                    break
                
                if pos['retrogrado'] and not em_retrogradacao:
                    # Início da retrogradação
                    inicio_retro = data_atual
                    em_retrogradacao = True
                
                elif not pos['retrogrado'] and em_retrogradacao:
                    # Fim da retrogradação
                    retrogradacoes.append({
                        'data_inicio': inicio_retro.strftime('%Y-%m-%d'),
                        'data_fim': data_atual.strftime('%Y-%m-%d'),
                        'signo_retrogradacao': pos['signo']
                    })
                    em_retrogradacao = False
                    break  # Apenas 1 retrogradação
                
                data_atual += timedelta(days=5)  # Verificar a cada 5 dias (mais rápido)
            
            return retrogradacoes
            
        except Exception as e:
            logger.error(f"Erro ao calcular retrogradações reais: {e}")
            return []
    
    def calcular_aspectos_natais(self, planeta_nome: str, planetas_natais: List[PlanetaInput]) -> List[Dict[str, Any]]:
        """Calcula apenas os aspectos mais relevantes (máximo 5 por planeta)"""
        try:
            aspectos = []
            hoje = datetime.now()
            
            # Verificar apenas 4 datas-chave no ano (reduzir drasticamente)
            datas_chave = [0, 90, 180, 270]  # A cada 3 meses
            
            for dias in datas_chave:
                data_teste = hoje + timedelta(days=dias)
                pos = self.calcular_posicao_real(planeta_nome, data_teste)
                
                if not pos:
                    continue
                
                for planeta_natal in planetas_natais:
                    diferenca = abs(pos['longitude'] - planeta_natal.fullDegree)
                    if diferenca > 180:
                        diferenca = 360 - diferenca
                    
                    for angulo, nome_aspecto, orbe in self.aspectos_maiores:
                        if abs(diferenca - angulo) <= orbe:
                            # Verificar se já temos este aspecto
                            existe = any(
                                a['planeta_natal'] == planeta_natal.name and
                                a['tipo_aspecto'] == nome_aspecto
                                for a in aspectos
                            )
                            
                            if not existe:
                                aspectos.append({
                                    'tipo_aspecto': nome_aspecto,
                                    'planeta_natal': planeta_natal.name,
                                    'casa_natal': planeta_natal.house,
                                    'data_aproximada': data_teste.strftime('%Y-%m-%d'),
                                    'orbe': round(abs(diferenca - angulo), 1)
                                })
            
            # LIMITAR a máximo 5 aspectos por planeta (os mais exatos)
            aspectos.sort(key=lambda x: x['orbe'])
            return aspectos[:5]
            
        except Exception as e:
            logger.error(f"Erro ao calcular aspectos natais: {e}")
            return []
    
    def processar_transito_especifico(self, planeta_nome: str, dados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa trânsito específico de um planeta"""
        try:
            # Separar dados
            transitos = dados[:11]
            natais = dados[11:22]
            casas_data = dados[22]
            
            # Encontrar planeta nos trânsitos
            planeta_transito = None
            for p in transitos:
                if p['name'] == planeta_nome:
                    planeta_transito = p
                    break
            
            if not planeta_transito:
                raise ValueError(f"Planeta {planeta_nome} não encontrado nos trânsitos")
            
            # Converter para modelos
            planetas_natais = [PlanetaInput(**p) for p in natais]
            casas = [CasaInput(**c) for c in casas_data['houses']]
            
            # Calcular usando dados REAIS
            casas_ativadas = self.calcular_mudancas_casa(planeta_nome, planeta_transito['sign'], casas)
            retrogradacoes = self.calcular_retrogradacoes_reais(planeta_nome)
            aspectos = self.calcular_aspectos_natais(planeta_nome, planetas_natais)
            
            return {
                'planeta': planeta_nome,
                'signo_atual': planeta_transito['sign'],
                'grau_atual': round(planeta_transito['normDegree'], 1),
                'casas_ativadas': casas_ativadas,
                'retrogradacoes': retrogradacoes,
                'aspectos_natais': aspectos,
                'periodo_analise': '1 ano'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar trânsito específico: {e}")
            raise

# ============ ENDPOINTS ============
calc = TransitoCalculator()

@app.get("/")
async def root():
    return {
        "message": "API Trânsitos Específicos v3.0 - CORRIGIDA",
        "status": "FUNCIONANDO COM DADOS REAIS",
        "principais_mudanças": [
            "✅ Usa PyEphem para cálculos REAIS",
            "✅ Remove dados hardcoded",
            "✅ Output MÍNIMO focado",
            "✅ Apenas trânsitos específicos",
            "✅ Orbe 5° para aspectos",
            "✅ Período 1 ano",
            "✅ Casas com datas reais"
        ]
    }

@app.post("/transito-especifico")
async def analisar_transito_especifico(data: Dict[str, Any]):
    """
    Endpoint principal para análise de trânsitos específicos.
    Input: {"planeta": "Urano", "dados": [array com dados]}
    Output: Dados mínimos para LLM produzir análise VI. TRÂNSITOS ESPECÍFICOS
    """
    try:
        planeta_nome = data.get('planeta')
        dados = data.get('dados', [])
        
        if not planeta_nome or not dados:
            raise HTTPException(status_code=400, detail="Planeta e dados são obrigatórios")
        
        if len(dados) < 23:
            raise HTTPException(status_code=400, detail="Dados insuficientes (mínimo 23 elementos)")
        
        logger.info(f"Processando trânsito específico: {planeta_nome}")
        
        resultado = calc.processar_transito_especifico(planeta_nome, dados)
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro no endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transitos-minimo")
async def transitos_output_minimo(data: List[Dict[str, Any]]):
    """
    Endpoint otimizado para todos os planetas relevantes.
    Output mínimo para LLM.
    """
    try:
        planetas_relevantes = ['Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão']
        resultados = {}
        
        for planeta in planetas_relevantes:
            try:
                resultado = calc.processar_transito_especifico(planeta, data)
                resultados[planeta] = resultado
            except Exception as e:
                logger.warning(f"Erro ao processar {planeta}: {e}")
                continue
        
        return {
            'planetas': resultados,
            'periodo_analise': '1 ano',
            'orbe_aspectos': '5 graus'
        }
        
    except Exception as e:
        logger.error(f"Erro no endpoint mínimo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 API Trânsitos Específicos v3.0 - CORRIGIDA")
    print("✅ Usa PyEphem para cálculos REAIS")
    print("✅ Remove dados hardcoded")
    print("✅ Output MÍNIMO focado")
    print("✅ Apenas para análise VI. TRÂNSITOS ESPECÍFICOS")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)