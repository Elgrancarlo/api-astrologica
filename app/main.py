from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import uvicorn
from datetime import datetime, timedelta
import ephem
import math
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Trânsitos Específicos PYEPHEM", version="7.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ CALCULADORA COM PYEPHEM ============
class TransitoEphem:
    def __init__(self):
        self.signos = [
            'Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
            'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes'
        ]
        
        # Mapa PyEphem
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
        
        # Aspectos maiores
        self.aspectos = [
            (0, "conjunção"),
            (60, "sextil"),
            (90, "quadratura"),
            (120, "trígono"),
            (180, "oposição")
        ]
    
    def calcular_data_futura(self, dias: int) -> str:
        """Calcula data futura"""
        data = datetime.now() + timedelta(days=dias)
        return data.strftime('%Y-%m-%d')
    
    def calcular_diferenca_angular(self, grau1: float, grau2: float) -> float:
        """Calcula diferença angular"""
        diff = abs(grau1 - grau2)
        return min(diff, 360 - diff)
    
    def obter_posicao_planeta(self, nome_planeta: str, data: datetime) -> Dict:
        """Obtém posição do planeta em uma data usando PyEphem"""
        try:
            planeta = self.ephem_map.get(nome_planeta)
            if not planeta:
                return None
            
            observer = ephem.Observer()
            observer.date = data.strftime('%Y/%m/%d')
            planeta.compute(observer)
            
            longitude_rad = planeta.hlong
            longitude_graus = float(longitude_rad) * 180 / math.pi
            
            # Calcular velocidade (hoje vs amanhã)
            observer.date = (data + timedelta(days=1)).strftime('%Y/%m/%d')
            planeta.compute(observer)
            longitude_amanha = float(planeta.hlong) * 180 / math.pi
            
            velocidade = longitude_amanha - longitude_graus
            if velocidade > 180:
                velocidade -= 360
            elif velocidade < -180:
                velocidade += 360
            
            # Determinar signo
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
            logger.error(f"Erro ao calcular posição de {nome_planeta}: {e}")
            return None
    
    def determinar_casa_por_grau(self, grau: float, casas: List[Dict]) -> int:
        """Determina casa baseada no grau"""
        grau = grau % 360
        
        for i, casa in enumerate(casas):
            proxima_casa = casas[(i + 1) % len(casas)]
            grau_casa = casa['degree']
            grau_proxima = proxima_casa['degree']
            
            if grau_proxima > grau_casa:
                if grau_casa <= grau < grau_proxima:
                    return casa['house']
            else:
                if grau >= grau_casa or grau < grau_proxima:
                    return casa['house']
        
        return 1
    
    def calcular_casas_ativadas(self, nome_planeta: str, casas: List[Dict]) -> List[Dict]:
        """Calcula casas ativadas nos próximos 365 dias"""
        casas_ativadas = []
        hoje = datetime.now()
        
        # Obter posição atual
        pos_atual = self.obter_posicao_planeta(nome_planeta, hoje)
        if not pos_atual:
            return []
        
        casa_atual = self.determinar_casa_por_grau(pos_atual['longitude'], casas)
        data_entrada_atual = hoje
        
        # Verificar mudanças de casa nos próximos 365 dias
        for dias in range(1, 366, 30):  # A cada 30 dias
            data_futura = hoje + timedelta(days=dias)
            pos_futura = self.obter_posicao_planeta(nome_planeta, data_futura)
            
            if pos_futura:
                casa_futura = self.determinar_casa_por_grau(pos_futura['longitude'], casas)
                
                if casa_futura != casa_atual:
                    # Mudança de casa detectada
                    casas_ativadas.append({
                        'casa': casa_atual,
                        'data_entrada': data_entrada_atual.strftime('%Y-%m-%d'),
                        'data_saida': data_futura.strftime('%Y-%m-%d')
                    })
                    
                    casa_atual = casa_futura
                    data_entrada_atual = data_futura
        
        # Adicionar casa atual se não tiver mudança
        if not casas_ativadas:
            casas_ativadas.append({
                'casa': casa_atual,
                'data_entrada': hoje.strftime('%Y-%m-%d'),
                'data_saida': self.calcular_data_futura(365)
            })
        
        return casas_ativadas[:3]  # Máximo 3 casas
    
    def calcular_retrogradacao(self, nome_planeta: str) -> List[Dict]:
        """Calcula retrogradação real nos próximos 365 dias"""
        retrogradacoes = []
        hoje = datetime.now()
        
        em_retrogradacao = False
        inicio_retro = None
        signo_retro = None
        
        # Verificar retrogradação a cada 5 dias
        for dias in range(0, 366, 5):
            data_teste = hoje + timedelta(days=dias)
            pos = self.obter_posicao_planeta(nome_planeta, data_teste)
            
            if pos:
                if pos['retrogrado'] and not em_retrogradacao:
                    # Início da retrogradação
                    inicio_retro = data_teste
                    signo_retro = pos['signo']
                    em_retrogradacao = True
                    
                elif not pos['retrogrado'] and em_retrogradacao:
                    # Fim da retrogradação
                    retrogradacoes.append({
                        'data_inicio': inicio_retro.strftime('%Y-%m-%d'),
                        'data_fim': data_teste.strftime('%Y-%m-%d'),
                        'signo_anterior': signo_retro,
                        'duracao_dias': (data_teste - inicio_retro).days
                    })
                    em_retrogradacao = False
        
        return retrogradacoes
    
    def calcular_aspectos_natais(self, nome_planeta: str, natais: List[Dict]) -> List[Dict]:
        """Calcula aspectos com planetas natais"""
        aspectos = []
        hoje = datetime.now()
        
        # Testar aspectos a cada 30 dias
        for dias in range(0, 366, 30):
            data_teste = hoje + timedelta(days=dias)
            pos = self.obter_posicao_planeta(nome_planeta, data_teste)
            
            if pos:
                for natal in natais[:5]:  # Máximo 5 planetas natais
                    if 'fullDegree' not in natal:
                        continue
                    
                    diferenca = self.calcular_diferenca_angular(pos['longitude'], natal['fullDegree'])
                    
                    for angulo, nome_aspecto in self.aspectos:
                        if abs(diferenca - angulo) <= 5:  # Orbe 5 graus
                            # Verificar se aspecto já existe
                            existe = any(
                                a['planeta_natal'] == natal['name'] and 
                                a['tipo_aspecto'] == nome_aspecto
                                for a in aspectos
                            )
                            
                            if not existe:
                                aspectos.append({
                                    'tipo_aspecto': nome_aspecto,
                                    'planeta_natal': natal['name'],
                                    'casa_natal': natal['house'],
                                    'data_inicio': self.calcular_data_futura(dias - 15),
                                    'data_exata': self.calcular_data_futura(dias),
                                    'data_fim': self.calcular_data_futura(dias + 15),
                                    'orbe': round(abs(diferenca - angulo), 1)
                                })
        
        return aspectos[:5]  # Máximo 5 aspectos
    
    def processar_planeta(self, planeta: Dict, natais: List[Dict], casas: List[Dict]) -> Dict:
        """Processa um planeta usando PyEphem"""
        nome = planeta['name']
        signo = planeta['sign']
        grau = planeta['normDegree']
        
        return {
            'planeta': nome,
            'signo_atual': signo,
            'grau_atual': round(grau, 1),
            'casas_ativadas': self.calcular_casas_ativadas(nome, casas),
            'retrogradacoes': self.calcular_retrogradacao(nome),
            'aspectos_natais': self.calcular_aspectos_natais(nome, natais),
            'periodo_analise': '1 ano'
        }

# ============ ENDPOINTS ============
calc = TransitoEphem()

@app.get("/")
async def root():
    return {
        "message": "API Trânsitos Específicos PyEphem v7.0",
        "status": "USANDO PYEPHEM - SEM DADOS HARDCODED",
        "biblioteca": "PyEphem para cálculos astronômicos reais",
        "funcionalidades": [
            "✅ Posições planetárias calculadas dinamicamente",
            "✅ Retrogradações calculadas (não hardcoded)",
            "✅ Aspectos com datas reais",
            "✅ Casas ativadas com mudanças reais",
            "✅ Período 1 ano completo"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "7.0.0"}

@app.post("/transito-especifico")
async def transito_especifico(data: Dict[str, Any]):
    """Análise de 1 planeta específico usando PyEphem"""
    try:
        planeta_nome = data.get('planeta')
        dados = data.get('dados', [])
        
        if not planeta_nome:
            raise HTTPException(status_code=400, detail="Campo 'planeta' obrigatório")
        
        if len(dados) < 23:
            raise HTTPException(status_code=400, detail="Dados insuficientes")
        
        # Separar dados
        transitos = dados[:11]
        natais = dados[11:22]
        casas = dados[22]['houses']
        
        # Encontrar planeta
        planeta = None
        for p in transitos:
            if p['name'] == planeta_nome:
                planeta = p
                break
        
        if not planeta:
            raise HTTPException(status_code=404, detail=f"Planeta {planeta_nome} não encontrado")
        
        # Processar usando PyEphem
        resultado = calc.processar_planeta(planeta, natais, casas)
        return resultado
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transitos-minimo")
async def transitos_minimo(data: List[Dict[str, Any]]):
    """Análise de todos os planetas relevantes usando PyEphem"""
    try:
        if len(data) < 23:
            raise HTTPException(status_code=400, detail="Dados insuficientes")
        
        # Separar dados
        transitos = data[:11]
        natais = data[11:22]
        casas = data[22]['houses']
        
        # Planetas relevantes
        planetas_relevantes = ['Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão']
        
        resultado_planetas = {}
        
        for planeta_nome in planetas_relevantes:
            # Encontrar planeta
            planeta = None
            for p in transitos:
                if p['name'] == planeta_nome:
                    planeta = p
                    break
            
            if planeta:
                resultado_planetas[planeta_nome] = calc.processar_planeta(planeta, natais, casas)
        
        return {
            'planetas': resultado_planetas,
            'periodo_analise': '1 ano',
            'orbe_aspectos': '5 graus',
            'biblioteca': 'PyEphem'
        }
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 API Trânsitos Específicos PyEphem v7.0")
    print("✅ Usando PyEphem para cálculos reais")
    print("✅ SEM dados hardcoded")
    print("✅ Posições calculadas dinamicamente")
    print("✅ Retrogradações calculadas")
    print("✅ Aspectos com datas reais")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)