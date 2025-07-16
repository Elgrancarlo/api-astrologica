from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import logging

# Importar ephem de forma segura
try:
    import ephem
    import math
    EPHEM_DISPONIVEL = True
except ImportError:
    EPHEM_DISPONIVEL = False
    logging.warning("PyEphem não disponível - usando cálculos simplificados")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Trânsitos Específicos DEBUG", version="7.0.0")

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
        
        # Mapa PyEphem (se disponível)
        if EPHEM_DISPONIVEL:
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
        else:
            self.ephem_map = {}
            logger.warning("PyEphem não disponível - retrogradações serão limitadas")
        
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
        """Obtém posição do planeta em uma data usando PyEphem (se disponível)"""
        if not EPHEM_DISPONIVEL:
            logger.warning("PyEphem não disponível - retornando None")
            return None
            
        try:
            planeta = self.ephem_map.get(nome_planeta)
            if not planeta:
                logger.warning(f"Planeta {nome_planeta} não encontrado no mapa PyEphem")
                return None
            
            observer = ephem.Observer()
            observer.date = data.strftime('%Y/%m/%d')
            planeta.compute(observer)
            
            longitude_rad = planeta.hlong
            longitude_graus = float(longitude_rad) * 180 / math.pi
            
            if longitude_graus < 0:
                longitude_graus += 360
            
            # Calcular velocidade simples (hoje vs amanhã)
            try:
                observer.date = (data + timedelta(days=1)).strftime('%Y/%m/%d')
                planeta.compute(observer)
                longitude_amanha = float(planeta.hlong) * 180 / math.pi
                
                if longitude_amanha < 0:
                    longitude_amanha += 360
                
                velocidade = longitude_amanha - longitude_graus
                if velocidade > 180:
                    velocidade -= 360
                elif velocidade < -180:
                    velocidade += 360
                    
            except Exception as e:
                logger.warning(f"Erro ao calcular velocidade para {nome_planeta}: {e}")
                velocidade = 0.1  # Fallback
            
            # Determinar signo
            signo_index = int(longitude_graus // 30) % 12
            grau_no_signo = longitude_graus % 30
            
            return {
                'longitude': longitude_graus,
                'signo': self.signos[signo_index],
                'grau_no_signo': grau_no_signo,
                'velocidade': velocidade,
                'retrogrado': velocidade < 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter posição de {nome_planeta}: {e}")
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
        """Calcula retrogradação usando PyEphem (se disponível)"""
        if not EPHEM_DISPONIVEL:
            logger.warning("PyEphem não disponível - retrogradações limitadas")
            return []
            
        try:
            if nome_planeta not in self.ephem_map:
                return []
            
            retrogradacoes = []
            hoje = datetime.now()
            
            em_retrogradacao = False
            inicio_retro = None
            
            # Verificar retrogradação a cada 15 dias (mais rápido)
            for dias in range(0, 366, 15):
                data_teste = hoje + timedelta(days=dias)
                pos = self.obter_posicao_planeta(nome_planeta, data_teste)
                
                if pos:
                    if pos['retrogrado'] and not em_retrogradacao:
                        # Início da retrogradação
                        inicio_retro = data_teste
                        em_retrogradacao = True
                        
                    elif not pos['retrogrado'] and em_retrogradacao:
                        # Fim da retrogradação
                        retrogradacoes.append({
                            'data_inicio': inicio_retro.strftime('%Y-%m-%d'),
                            'data_fim': data_teste.strftime('%Y-%m-%d'),
                            'signo_anterior': pos['signo'],  # Usar signo atual como aproximação
                            'duracao_dias': (data_teste - inicio_retro).days
                        })
                        em_retrogradacao = False
                        
                        # Parar após encontrar uma retrogradação
                        break
            
            return retrogradacoes
            
        except Exception as e:
            logger.error(f"Erro ao calcular retrogradação de {nome_planeta}: {e}")
            return []
    
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
        
    def calcular_casas_com_dados_entrada(self, planeta: Dict, casas: List[Dict]) -> List[Dict]:
        """Calcula casas usando dados de entrada (mais simples e confiável)"""
        try:
            signo = planeta.get('sign', 'Áries')
            grau_atual = float(planeta.get('normDegree', 0))
            casa_atual = int(planeta.get('house', 1))
            velocidade = abs(float(planeta.get('speed', 0.1)))
            
            if velocidade == 0:
                velocidade = 0.1  # Fallback
            
            # Posição atual absoluta
            try:
                signo_index = self.signos.index(signo)
            except ValueError:
                return [{'casa': casa_atual, 'data_entrada': self.calcular_data_futura(0)}]
            
            grau_inicio_signo = signo_index * 30
            grau_absoluto_atual = grau_inicio_signo + grau_atual
            
            casas_ativadas = []
            
            # Casa atual
            casa_calculada = self.determinar_casa_por_grau(grau_absoluto_atual, casas)
            casas_ativadas.append({
                'casa': casa_calculada,
                'data_entrada': self.calcular_data_futura(0),
                'data_saida': None
            })
            
            # Próximas casas no signo (simplificado)
            graus_teste = [grau_absoluto_atual + 10, grau_absoluto_atual + 20]
            grau_fim_signo = grau_inicio_signo + 30
            
            for grau_teste in graus_teste:
                if grau_teste < grau_fim_signo:  # Ainda no mesmo signo
                    casa_teste = self.determinar_casa_por_grau(grau_teste, casas)
                    
                    if casa_teste != casa_calculada:
                        dias_ate_casa = int((grau_teste - grau_absoluto_atual) / velocidade)
                        
                        # Fechar casa anterior
                        if casas_ativadas:
                            casas_ativadas[-1]['data_saida'] = self.calcular_data_futura(dias_ate_casa)
                        
                        # Nova casa
                        casas_ativadas.append({
                            'casa': casa_teste,
                            'data_entrada': self.calcular_data_futura(dias_ate_casa),
                            'data_saida': None
                        })
                        
                        casa_calculada = casa_teste
            
            # Fechar última casa
            if casas_ativadas:
                dias_ate_fim = int((grau_fim_signo - grau_absoluto_atual) / velocidade)
                casas_ativadas[-1]['data_saida'] = self.calcular_data_futura(dias_ate_fim)
            
            return casas_ativadas[:3]  # Máximo 3
            
        except Exception as e:
            logger.error(f"Erro em calcular_casas_com_dados_entrada: {e}")
            return [{'casa': planeta.get('house', 1), 'data_entrada': self.calcular_data_futura(0)}]
    
    def calcular_aspectos_com_dados_entrada(self, planeta: Dict, natais: List[Dict]) -> List[Dict]:
        """Calcula aspectos usando dados de entrada"""
        try:
            signo = planeta.get('sign', 'Áries')
            grau_atual = float(planeta.get('normDegree', 0))
            velocidade = abs(float(planeta.get('speed', 0.1)))
            
            # Posição atual absoluta
            try:
                signo_index = self.signos.index(signo)
            except ValueError:
                return []
            
            grau_absoluto = (signo_index * 30) + grau_atual
            
            aspectos = []
            
            # Testar posições futuras (simplificado: 4 pontos no ano)
            for dias in [0, 90, 180, 270]:  # A cada 3 meses
                grau_futuro = grau_absoluto + (velocidade * dias)
                grau_futuro = grau_futuro % 360
                
                for natal in natais[:5]:  # Máximo 5 planetas natais
                    if not isinstance(natal, dict) or 'fullDegree' not in natal:
                        continue
                    
                    try:
                        natal_grau = float(natal.get('fullDegree', 0))
                        diferenca = self.calcular_diferenca_angular(grau_futuro, natal_grau)
                        
                        for angulo, nome_aspecto in self.aspectos:
                            if abs(diferenca - angulo) <= 5:  # Orbe 5 graus
                                # Verificar se aspecto já existe
                                existe = any(
                                    a.get('planeta_natal') == natal.get('name') and 
                                    a.get('tipo_aspecto') == nome_aspecto
                                    for a in aspectos
                                )
                                
                                if not existe:
                                    aspectos.append({
                                        'tipo_aspecto': nome_aspecto,
                                        'planeta_natal': natal.get('name', 'Desconhecido'),
                                        'casa_natal': int(natal.get('house', 1)),
                                        'data_inicio': self.calcular_data_futura(dias - 15),
                                        'data_exata': self.calcular_data_futura(dias),
                                        'data_fim': self.calcular_data_futura(dias + 15),
                                        'orbe': round(abs(diferenca - angulo), 1)
                                    })
                    except Exception as e:
                        logger.warning(f"Erro ao processar aspecto com {natal.get('name', 'Desconhecido')}: {e}")
                        continue
            
            # Ordenar e limitar
            aspectos.sort(key=lambda x: x.get('data_exata', ''))
            return aspectos[:5]
            
        except Exception as e:
            logger.error(f"Erro em calcular_aspectos_com_dados_entrada: {e}")
            return []
    
    def processar_planeta(self, planeta: Dict, natais: List[Dict], casas: List[Dict]) -> Dict:
        """Processa um planeta usando dados de entrada + PyEphem quando necessário"""
        try:
            nome = planeta.get('name', 'Desconhecido')
            signo = planeta.get('sign', 'Áries')
            grau = float(planeta.get('normDegree', 0))
            velocidade = float(planeta.get('speed', 0))
            eh_retrogrado = str(planeta.get('isRetro', 'false')).lower() == 'true'
            
            logger.info(f"Processando {nome}: {signo} {grau:.1f}°, velocidade: {velocidade:.4f}, retro: {eh_retrogrado}")
            
            # Usar dados de entrada diretamente quando possível
            resultado = {
                'planeta': nome,
                'signo_atual': signo,
                'grau_atual': round(grau, 1),
                'casas_ativadas': [],
                'retrogradacoes': [],
                'aspectos_natais': [],
                'periodo_analise': '1 ano'
            }
            
            # Calcular casas ativadas usando dados existentes
            try:
                resultado['casas_ativadas'] = self.calcular_casas_com_dados_entrada(planeta, casas)
            except Exception as e:
                logger.error(f"Erro ao calcular casas para {nome}: {e}")
                resultado['casas_ativadas'] = [{'casa': planeta.get('house', 1), 'data_entrada': self.calcular_data_futura(0)}]
            
            # Calcular retrogradação usando PyEphem se necessário
            try:
                if eh_retrogrado or velocidade < 0:
                    resultado['retrogradacoes'] = self.calcular_retrogradacao(nome)
                else:
                    resultado['retrogradacoes'] = []
            except Exception as e:
                logger.error(f"Erro ao calcular retrogradação para {nome}: {e}")
                resultado['retrogradacoes'] = []
            
            # Calcular aspectos natais
            try:
                resultado['aspectos_natais'] = self.calcular_aspectos_com_dados_entrada(planeta, natais)
            except Exception as e:
                logger.error(f"Erro ao calcular aspectos para {nome}: {e}")
                resultado['aspectos_natais'] = []
            
            logger.info(f"Planeta {nome} processado: {len(resultado['casas_ativadas'])} casas, {len(resultado['retrogradacoes'])} retros, {len(resultado['aspectos_natais'])} aspectos")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro geral ao processar planeta: {e}")
            return {
                'planeta': planeta.get('name', 'Desconhecido'),
                'erro': str(e),
                'signo_atual': planeta.get('sign', 'Áries'),
                'grau_atual': round(float(planeta.get('normDegree', 0)), 1),
                'casas_ativadas': [],
                'retrogradacoes': [],
                'aspectos_natais': [],
                'periodo_analise': '1 ano'
            }

# ============ ENDPOINTS ============
calc = TransitoEphem()

@app.get("/")
async def root():
    return {
        "message": "API Trânsitos Específicos DEBUG v7.0",
        "status": "CÓDIGO CORRIGIDO COM DEBUG DETALHADO",
        "biblioteca": "PyEphem + dados de entrada híbrido",
        "principais_correcoes": [
            "✅ Verificações robustas no elemento 22",
            "✅ Logging detalhado para identificar erros",
            "✅ Uso híbrido: dados de entrada + PyEphem",
            "✅ Tratamento de erro individual por planeta",
            "✅ Fallbacks para todos os cálculos",
            "✅ Processamento não quebra se um planeta falha"
        ],
        "funcionalidades": [
            "✅ Casas ativadas usando dados de entrada",
            "✅ Retrogradações calculadas com PyEphem",
            "✅ Aspectos com datas calculadas",
            "✅ Período 1 ano completo",
            "✅ Debug detalhado no log"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

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
        logger.info(f"=== DEBUG INÍCIO ===")
        logger.info(f"Recebidos {len(data)} elementos")
        
        if len(data) < 23:
            raise HTTPException(status_code=400, detail=f"Dados insuficientes: {len(data)} elementos (mínimo 23)")
        
        # DEBUG: Verificar elemento 22 detalhadamente
        logger.info(f"=== VERIFICANDO ELEMENTO 22 ===")
        elemento_22 = data[22]
        logger.info(f"Tipo do elemento 22: {type(elemento_22)}")
        
        if elemento_22 is None:
            raise HTTPException(status_code=400, detail="Elemento 22 é None")
        
        if not isinstance(elemento_22, dict):
            raise HTTPException(status_code=400, detail=f"Elemento 22 não é dict: {type(elemento_22)}")
        
        logger.info(f"Keys do elemento 22: {list(elemento_22.keys())}")
        
        if 'houses' not in elemento_22:
            raise HTTPException(status_code=400, detail=f"Chave 'houses' não encontrada. Keys disponíveis: {list(elemento_22.keys())}")
        
        casas = elemento_22['houses']
        logger.info(f"Tipo de 'houses': {type(casas)}")
        logger.info(f"Número de casas: {len(casas) if isinstance(casas, list) else 'não é lista'}")
        
        if not isinstance(casas, list):
            raise HTTPException(status_code=400, detail=f"'houses' não é lista: {type(casas)}")
        
        if len(casas) < 12:
            raise HTTPException(status_code=400, detail=f"Número insuficiente de casas: {len(casas)}")
        
        # Separar dados
        transitos = data[:11]
        natais = data[11:22]
        
        logger.info(f"Transitos: {len(transitos)} elementos")
        logger.info(f"Natais: {len(natais)} elementos")
        logger.info(f"Casas: {len(casas)} elementos")
        
        # DEBUG: Verificar planetas nos trânsitos
        planetas_encontrados = [p.get('name') for p in transitos if p and p.get('name')]
        logger.info(f"Planetas encontrados nos trânsitos: {planetas_encontrados}")
        
        # Planetas relevantes
        planetas_relevantes = ['Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão']
        
        resultado_planetas = {}
        
        for planeta_nome in planetas_relevantes:
            try:
                logger.info(f"=== PROCESSANDO {planeta_nome} ===")
                
                # Encontrar planeta
                planeta = None
                for p in transitos:
                    if p and p.get('name') == planeta_nome:
                        planeta = p
                        break
                
                if planeta:
                    logger.info(f"Planeta {planeta_nome} encontrado: {planeta.get('sign')} {planeta.get('normDegree'):.1f}°")
                    resultado_planetas[planeta_nome] = calc.processar_planeta(planeta, natais, casas)
                    logger.info(f"Planeta {planeta_nome} processado com sucesso")
                else:
                    logger.warning(f"Planeta {planeta_nome} não encontrado nos trânsitos")
                    
            except Exception as e:
                logger.error(f"Erro ao processar {planeta_nome}: {str(e)}")
                # Continuar com próximo planeta ao invés de quebrar tudo
                resultado_planetas[planeta_nome] = {
                    'planeta': planeta_nome,
                    'erro': str(e),
                    'signo_atual': 'N/A',
                    'grau_atual': 0,
                    'casas_ativadas': [],
                    'retrogradacoes': [],
                    'aspectos_natais': [],
                    'periodo_analise': '1 ano'
                }
        
        logger.info(f"=== RESULTADO FINAL ===")
        logger.info(f"Planetas processados: {len(resultado_planetas)}")
        
        return {
            'planetas': resultado_planetas,
            'periodo_analise': '1 ano',
            'orbe_aspectos': '5 graus',
            'biblioteca': 'PyEphem',
            'debug_info': {
                'total_elementos': len(data),
                'planetas_encontrados': planetas_encontrados,
                'planetas_processados': len(resultado_planetas)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro geral: {str(e)}")
        logger.error(f"Tipo do erro: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

if __name__ == "__main__":
    print("🚀 API Trânsitos Específicos DEBUG v7.0")
    print("🔍 CÓDIGO CORRIGIDO COM DEBUG DETALHADO")
    print("✅ Verificações robustas no acesso a 'houses'")
    print("✅ Logging detalhado para identificar problemas")
    print("✅ Uso híbrido: dados de entrada + PyEphem")
    print("✅ Tratamento de erro robusto")
    print("✅ Processamento não quebra se um planeta falha")
    print("🔧 Agora deve identificar exatamente onde está o erro")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)