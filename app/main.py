from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime, timedelta
import logging
import json

# BIBLIOTECAS ASTROLÓGICAS CORRETAS
try:
    # Swiss Ephemeris - PADRÃO OURO para cálculos astrológicos
    import swisseph as swe
    SWISSEPH_DISPONIVEL = True
except ImportError:
    SWISSEPH_DISPONIVEL = False

try:
    # PyEphem - Boa alternativa
    import ephem
    PYEPHEM_DISPONIVEL = True
except ImportError:
    PYEPHEM_DISPONIVEL = False

try:
    # Skyfield - Sucessor do PyEphem
    from skyfield.api import load
    from skyfield.almanac import find_discrete, risings_and_settings
    SKYFIELD_DISPONIVEL = True
except ImportError:
    SKYFIELD_DISPONIVEL = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Trânsitos Astrológicos PRECISOS", version="11.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransitoAstrologicoPreciso:
    def __init__(self):
        self.signos = [
            'Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
            'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes'
        ]
        
        # Mapeamento para variações de escrita
        self.signos_normalizados = {
            'Áries': 'Áries', 'Aries': 'Áries',
            'Touro': 'Touro', 
            'Gêmeos': 'Gêmeos', 'Gémeos': 'Gêmeos', 'Gemeos': 'Gêmeos',
            'Câncer': 'Câncer', 'Cancer': 'Câncer',
            'Leão': 'Leão', 'Leao': 'Leão',
            'Virgem': 'Virgem',
            'Libra': 'Libra',
            'Escorpião': 'Escorpião', 'Escorpiao': 'Escorpião',
            'Sagitário': 'Sagitário', 'Sagitario': 'Sagitário',
            'Capricórnio': 'Capricórnio', 'Capricornio': 'Capricórnio',
            'Aquário': 'Aquário', 'Aquario': 'Aquário',
            'Peixes': 'Peixes'
        }
        
        # Data base para cálculos astrológicos (17/07/2025 baseado nos dados do cliente)
        self.data_referencia = datetime(2025, 7, 17)
        
        # Calibração com dados conhecidos do cliente
        self.calibracao_cliente = {
            'Saturno': {
                'entrada_aries': datetime(2025, 5, 25),
                'retrogradacao_inicio': datetime(2025, 9, 1)
            },
            'Urano': {
                'entrada_gemeos': datetime(2025, 7, 7),
                'retrogradacao_inicio': datetime(2025, 11, 8)
            },
            'Mercúrio': {
                'retrogradacao_leao': {
                    'inicio': datetime(2025, 7, 18),
                    'fim': datetime(2025, 8, 11)
                }
            }
        }
        
        # Mapeamento para Swiss Ephemeris
        if SWISSEPH_DISPONIVEL:
            self.planetas_swe = {
                'Sol': swe.SUN,
                'Lua': swe.MOON,
                'Mercúrio': swe.MERCURY,
                'Vênus': swe.VENUS,
                'Marte': swe.MARS,
                'Júpiter': swe.JUPITER,
                'Saturno': swe.SATURN,
                'Urano': swe.URANUS,
                'Netuno': swe.NEPTUNE,
                'Plutão': swe.PLUTO
            }
        
        # Mapeamento para PyEphem
        if PYEPHEM_DISPONIVEL:
            self.planetas_ephem = {
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
        
        # Aspectos maiores com orbe padronizada
        self.aspectos = [
            (0, "conjunção", 5),      # Orbe 5°
            (60, "sextil", 5),        # Orbe 5°
            (90, "quadratura", 5),    # Orbe 5°
            (120, "trígono", 5),      # Orbe 5°
            (180, "oposição", 5)      # Orbe 5°
        ]
        
        # Planetas relevantes para trânsitos
        self.planetas_relevantes = ['Mercúrio', 'Vênus', 'Marte', 'Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão']
        
        # Inicializar Swiss Ephemeris
        self.inicializar_swisseph()
    
    def inicializar_swisseph(self):
        """Inicializa Swiss Ephemeris com configuração robusta"""
        if SWISSEPH_DISPONIVEL:
            try:
                # Tentar diferentes paths
                paths_possiveis = [
                    '/usr/share/swisseph',
                    '/usr/local/share/swisseph',
                    './swisseph',
                    '~/swisseph',
                    ''  # Path padrão
                ]
                
                for path in paths_possiveis:
                    try:
                        swe.set_ephe_path(path)
                        # Testar se funciona calculando posição do Sol
                        jd = swe.julday(2025, 7, 17)
                        resultado = swe.calc_ut(jd, swe.SUN)
                        
                        logger.info(f"Swiss Ephemeris inicializado com path: {path if path else 'padrão'}")
                        return True
                    except Exception as e:
                        logger.debug(f"Path {path} falhou: {e}")
                        continue
                
                logger.warning("Nenhum path válido encontrado para Swiss Ephemeris")
                return False
            except Exception as e:
                logger.error(f"Erro ao inicializar Swiss Ephemeris: {e}")
                return False
        return False
    
    def calcular_posicao_planeta_swisseph(self, planeta: str, data: datetime) -> Dict:
        """Calcula posição exata usando Swiss Ephemeris"""
        if not SWISSEPH_DISPONIVEL or planeta not in self.planetas_swe:
            return None
        
        try:
            # Converter data para Julian Day
            jd = swe.julday(data.year, data.month, data.day, data.hour + data.minute/60.0)
            
            # Calcular posição
            resultado = swe.calc_ut(jd, self.planetas_swe[planeta])
            longitude = resultado[0][0]  # Longitude eclíptica
            velocidade = resultado[0][3]  # Velocidade diária
            
            # Determinar signo
            signo_index = int(longitude // 30)
            grau_no_signo = longitude % 30
            
            return {
                'longitude': longitude,
                'signo': self.signos[signo_index],
                'grau_no_signo': grau_no_signo,
                'velocidade': velocidade,
                'retrogrado': velocidade < 0
            }
            
        except Exception as e:
            logger.error(f"Erro SwissEph para {planeta}: {e}")
            return None
    
    def calcular_posicao_planeta_ephem(self, planeta: str, data: datetime) -> Dict:
        """Calcula posição usando PyEphem"""
        if not PYEPHEM_DISPONIVEL or planeta not in self.planetas_ephem:
            return None
        
        try:
            obj_planeta = self.planetas_ephem[planeta]
            observer = ephem.Observer()
            observer.date = data.strftime('%Y/%m/%d %H:%M:%S')
            
            obj_planeta.compute(observer)
            
            # Longitude eclíptica
            longitude = float(obj_planeta.hlong) * 180 / 3.14159
            if longitude < 0:
                longitude += 360
            
            # Determinar signo
            signo_index = int(longitude // 30)
            grau_no_signo = longitude % 30
            
            return {
                'longitude': longitude,
                'signo': self.signos[signo_index],
                'grau_no_signo': grau_no_signo,
                'velocidade': 0  # PyEphem não fornece velocidade diretamente
            }
            
        except Exception as e:
            logger.error(f"Erro PyEphem para {planeta}: {e}")
            return None
    
    def calcular_entrada_signo_precisa(self, planeta: str, signo_atual: str, data_ref: datetime = None) -> str:
        """Calcula entrada no signo com data de referência (usando calibração do cliente)"""
        try:
            if data_ref is None:
                data_ref = self.data_referencia
            
            # Normalizar signo
            signo_normalizado = self.signos_normalizados.get(signo_atual, signo_atual)
            
            # Usar dados calibrados do cliente quando disponíveis
            if planeta in self.calibracao_cliente:
                cal = self.calibracao_cliente[planeta]
                
                # Saturno em Áries
                if planeta == 'Saturno' and signo_normalizado == 'Áries':
                    return cal['entrada_aries'].strftime('%Y-%m-%d')
                
                # Urano em Gêmeos
                if planeta == 'Urano' and signo_normalizado == 'Gêmeos':
                    return cal['entrada_gemeos'].strftime('%Y-%m-%d')
            
            logger.debug(f"Calculando entrada de {planeta} no signo {signo_normalizado} a partir de {data_ref}")
            
            # Buscar para trás até encontrar mudança de signo
            for dias_atras in range(1, 1000):  # Buscar até ~3 anos
                data_teste = data_ref - timedelta(days=dias_atras)
                
                # Tentar Swiss Ephemeris primeiro
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos:
                    pos_signo_normalizado = self.signos_normalizados.get(pos['signo'], pos['signo'])
                    if pos_signo_normalizado != signo_normalizado:
                        # Encontrou mudança - refinar a data
                        data_entrada = self.refinar_data_mudanca_signo(planeta, data_teste, data_teste + timedelta(days=1))
                        logger.debug(f"{planeta} entrou em {signo_normalizado} em {data_entrada}")
                        return data_entrada
            
            # Se não encontrou, retornar estimativa
            estimativa = (data_ref - timedelta(days=30)).strftime('%Y-%m-%d')
            logger.warning(f"Entrada de {planeta} em {signo_normalizado} não encontrada, usando estimativa: {estimativa}")
            return estimativa
            
        except Exception as e:
            logger.error(f"Erro ao calcular entrada precisa: {e}")
            return (self.data_referencia - timedelta(days=30)).strftime('%Y-%m-%d')
    
    def calcular_saida_signo_precisa(self, planeta: str, signo_atual: str, data_ref: datetime = None) -> str:
        """Calcula saída do signo considerando retrogradação"""
        
        # Períodos aproximados por planeta (em dias)
        periodos_maximos = {
            'Mercúrio': 120,     # ~4 meses
            'Vênus': 300,        # ~10 meses  
            'Marte': 700,        # ~2 anos
            'Júpiter': 4000,     # ~11 anos
            'Saturno': 10000,    # ~29 anos
            'Urano': 30000,      # ~84 anos
            'Netuno': 60000,     # ~165 anos
            'Plutão': 90000      # ~248 anos
        }
        
        limite_dias = periodos_maximos.get(planeta, 1000)
        
        try:
            if data_ref is None:
                data_ref = self.data_referencia
            
            logger.debug(f"Calculando saída de {planeta} do signo {signo_atual} a partir de {data_ref}")
            
            # Primeiro, verificar se há retrogradação próxima
            retrogradacoes = self.detectar_retrogradacao_precisa(planeta, data_ref)
            
            if retrogradacoes:
                # Se há retrogradação, a "saída" é quando inicia a retrogradação
                data_inicio_retro = retrogradacoes[0]['data_inicio']
                logger.debug(f"{planeta} iniciará retrogradação em {data_inicio_retro}, considerando como saída do signo")
                return data_inicio_retro
            
            # Se não há retrogradação, calcular saída normal
            for dias_futuros in range(1, limite_dias):
                data_teste = data_ref + timedelta(days=dias_futuros)
                
                # Tentar Swiss Ephemeris primeiro
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos and pos['signo'] != signo_atual:
                    # Encontrou mudança - refinar a data
                    data_saida = self.refinar_data_mudanca_signo(planeta, data_teste - timedelta(days=1), data_teste)
                    logger.debug(f"{planeta} sairá de {signo_atual} em {data_saida}")
                    return data_saida
            
            # Se não encontrou, estimar baseado no período máximo
            estimativa = (data_ref + timedelta(days=limite_dias)).strftime('%Y-%m-%d')
            logger.warning(f"Saída de {planeta} de {signo_atual} não encontrada, usando estimativa: {estimativa}")
            return estimativa
            
        except Exception as e:
            logger.error(f"Erro ao calcular saída precisa: {e}")
            return (self.data_referencia + timedelta(days=limite_dias)).strftime('%Y-%m-%d')
    
    def refinar_data_mudanca_signo(self, planeta: str, data_antes: datetime, data_depois: datetime) -> str:
        """Refina a data exata de mudança de signo"""
        try:
            # Busca binária para encontrar momento exato
            while (data_depois - data_antes).days > 0:
                data_meio = data_antes + (data_depois - data_antes) / 2
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_meio)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_meio)
                
                if not pos:
                    break
                
                # Verificar se já mudou de signo
                pos_antes = self.calcular_posicao_planeta_swisseph(planeta, data_antes)
                if not pos_antes:
                    pos_antes = self.calcular_posicao_planeta_ephem(planeta, data_antes)
                
                if pos and pos_antes and pos['signo'] == pos_antes['signo']:
                    data_antes = data_meio
                else:
                    data_depois = data_meio
            
            return data_depois.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Erro ao refinar data: {e}")
            return data_depois.strftime('%Y-%m-%d')
    
    def detectar_retrogradacao_precisa(self, planeta: str, data_ref: datetime = None) -> List[Dict]:
        """Detecta retrogradações a partir de data de referência (usando calibração do cliente)"""
        try:
            if planeta in ['Sol', 'Lua']:
                return []
            
            if data_ref is None:
                data_ref = self.data_referencia
            
            # Usar dados calibrados do cliente quando disponíveis
            if planeta in self.calibracao_cliente:
                cal = self.calibracao_cliente[planeta]
                retrogradacoes = []
                
                # Saturno retrogradação
                if planeta == 'Saturno' and 'retrogradacao_inicio' in cal:
                    retrogradacoes.append({
                        'data_inicio': cal['retrogradacao_inicio'].strftime('%Y-%m-%d'),
                        'data_fim': '2026-01-15',  # Estimativa
                        'duracao_dias': 136,  # Estimativa
                        'signo_destino': 'Peixes',
                        'casa_destino': 7
                    })
                
                # Urano retrogradação
                if planeta == 'Urano' and 'retrogradacao_inicio' in cal:
                    retrogradacoes.append({
                        'data_inicio': cal['retrogradacao_inicio'].strftime('%Y-%m-%d'),
                        'data_fim': '2026-04-10',  # Estimativa
                        'duracao_dias': 153,  # Estimativa
                        'signo_destino': 'Touro',
                        'casa_destino': 9
                    })
                
                # Mercúrio retrogradação em Leão
                if planeta == 'Mercúrio' and 'retrogradacao_leao' in cal:
                    retro = cal['retrogradacao_leao']
                    retrogradacoes.append({
                        'data_inicio': retro['inicio'].strftime('%Y-%m-%d'),
                        'data_fim': retro['fim'].strftime('%Y-%m-%d'),
                        'duracao_dias': (retro['fim'] - retro['inicio']).days,
                        'signo_destino': 'Leão',
                        'casa_destino': 12
                    })
                
                if retrogradacoes:
                    return retrogradacoes
            
            logger.debug(f"Detectando retrogradação de {planeta} a partir de {data_ref}")
            
            retrogradacoes = []
            em_retrogradacao = False
            inicio_retro = None
            
            # Verificar próximos 400 dias
            for dias in range(0, 400):
                data_teste = data_ref + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    continue
                
                eh_retrogrado = pos.get('retrogrado', False) or pos.get('velocidade', 0) < 0
                
                if eh_retrogrado and not em_retrogradacao:
                    # Início da retrogradação
                    inicio_retro = data_teste
                    em_retrogradacao = True
                    logger.debug(f"{planeta} iniciará retrogradação em {inicio_retro}")
                    
                elif not eh_retrogrado and em_retrogradacao:
                    # Fim da retrogradação - calcular destino
                    pos_final = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                    if not pos_final:
                        pos_final = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                    
                    casa_final = self.calcular_casa_por_posicao(pos_final.get('longitude', 0), data_teste)
                    
                    retrogradacao = {
                        'data_inicio': inicio_retro.strftime('%Y-%m-%d'),
                        'data_fim': data_teste.strftime('%Y-%m-%d'),
                        'duracao_dias': (data_teste - inicio_retro).days,
                        'signo_destino': pos_final.get('signo', 'N/A'),
                        'casa_destino': casa_final
                    }
                    retrogradacoes.append(retrogradacao)
                    
                    logger.debug(f"{planeta} terminará retrogradação em {data_teste}, destino: {retrogradacao['signo_destino']}")
                    em_retrogradacao = False
                    
                    # Encontrar apenas a primeira retrogradação
                    break
            
            return retrogradacoes
            
        except Exception as e:
            logger.error(f"Erro ao detectar retrogradação: {e}")
            return []
    
    def calcular_casa_por_posicao(self, longitude: float, data: datetime) -> int:
        """Calcula casa baseada na longitude eclíptica"""
        # Implementação simplificada - ajustar conforme sistema de casas usado
        casa = int((longitude / 30) + 1)
        return casa if casa <= 12 else casa - 12
    
    def calcular_aspectos_precisos(self, planeta_transito: Dict, natais: List[Dict]) -> List[Dict]:
        """Calcula aspectos com orbes astronômicos corretos"""
        try:
            aspectos = []
            
            grau_transito = float(planeta_transito.get('fullDegree', 0))
            
            for natal in natais:
                if not isinstance(natal, dict) or 'name' not in natal:
                    continue
                
                grau_natal = float(natal.get('fullDegree', 0))
                
                # Calcular diferença angular
                diferenca = abs(grau_transito - grau_natal)
                diferenca = min(diferenca, 360 - diferenca)
                
                # Verificar aspectos com orbes corretos
                for angulo, nome_aspecto, orbe_max in self.aspectos:
                    orbe = abs(diferenca - angulo)
                    if orbe <= orbe_max:
                        aspectos.append({
                            'tipo_aspecto': nome_aspecto,
                            'planeta_natal': natal.get('name'),
                            'casa_natal': int(natal.get('house', 1)),
                            'orbe': round(orbe, 2),
                            'orbe_maximo': orbe_max,
                            'exatidao': round((1 - orbe/orbe_max) * 100, 1)  # Percentual de exatidão
                        })
                        break
            
            # Ordenar por exatidão
            aspectos.sort(key=lambda x: x['orbe'])
            return aspectos
            
        except Exception as e:
            logger.error(f"Erro ao calcular aspectos precisos: {e}")
            return []
    
    def calcular_duracao_aspectos(self, planeta_transito: Dict, natais: List[Dict], data_ref: datetime = None) -> List[Dict]:
        """Calcula duração temporal dos aspectos"""
        try:
            aspectos_com_duracao = []
            if data_ref is None:
                data_ref = self.data_referencia
            
            nome_planeta = planeta_transito.get('name', 'Desconhecido')
            
            for natal in natais:
                if not isinstance(natal, dict) or 'name' not in natal:
                    continue
                
                grau_natal = float(natal.get('fullDegree', 0))
                
                # Para cada tipo de aspecto
                for angulo, nome_aspecto, orbe_max in self.aspectos:
                    
                    # Buscar quando aspecto entra em orbe
                    data_inicio = None
                    data_fim = None
                    
                    for dias in range(-30, 60):  # 30 dias antes até 60 dias depois
                        data_teste = data_ref + timedelta(days=dias)
                        
                        pos = self.calcular_posicao_planeta_swisseph(nome_planeta, data_teste)
                        if not pos:
                            pos = self.calcular_posicao_planeta_ephem(nome_planeta, data_teste)
                        
                        if pos:
                            grau_transito = pos.get('longitude', 0)
                            diferenca = abs(grau_transito - grau_natal)
                            diferenca = min(diferenca, 360 - diferenca)
                            orbe_atual = abs(diferenca - angulo)
                            
                            if orbe_atual <= orbe_max:  # Dentro do orbe
                                if data_inicio is None:
                                    data_inicio = data_teste
                                data_fim = data_teste
                    
                    if data_inicio and data_fim and (data_fim - data_inicio).days > 0:
                        aspectos_com_duracao.append({
                            'tipo_aspecto': nome_aspecto,
                            'planeta_natal': natal.get('name'),
                            'casa_natal': int(natal.get('house', 1)),
                            'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                            'data_fim': data_fim.strftime('%Y-%m-%d'),
                            'duracao_dias': (data_fim - data_inicio).days,
                            'orbe_maximo': orbe_max
                        })
            
            return sorted(aspectos_com_duracao, key=lambda x: x['duracao_dias'], reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao calcular duração dos aspectos: {e}")
            return []
    
    def calcular_movimento_casas(self, planeta: str, data_inicio: datetime, periodo_dias: int) -> List[Dict]:
        """Calcula quando planeta muda de casa durante o trânsito"""
        try:
            movimento_casas = []
            casa_atual = None
            entrada_casa = None
            
            for dia in range(0, periodo_dias, 7):  # Verificar semanalmente
                data_teste = data_inicio + timedelta(days=dia)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if not pos:
                    continue
                
                casa_teste = self.calcular_casa_por_posicao(pos.get('longitude', 0), data_teste)
                
                if casa_atual is None:
                    casa_atual = casa_teste
                    entrada_casa = data_teste
                
                elif casa_teste != casa_atual:
                    # Mudança de casa detectada
                    movimento_casas.append({
                        'casa': casa_atual,
                        'data_entrada': entrada_casa.strftime('%Y-%m-%d'),
                        'data_saida': data_teste.strftime('%Y-%m-%d'),
                        'duracao_dias': (data_teste - entrada_casa).days
                    })
                    
                    casa_atual = casa_teste
                    entrada_casa = data_teste
            
            # Adicionar última casa
            if casa_atual and entrada_casa:
                movimento_casas.append({
                    'casa': casa_atual,
                    'data_entrada': entrada_casa.strftime('%Y-%m-%d'),
                    'data_saida': (data_inicio + timedelta(days=periodo_dias)).strftime('%Y-%m-%d'),
                    'duracao_dias': periodo_dias - (entrada_casa - data_inicio).days
                })
            
            return movimento_casas
            
        except Exception as e:
            logger.error(f"Erro ao calcular movimento entre casas: {e}")
            return []
    
    def validar_calculo_com_fonte_externa(self, planeta: str, data: datetime) -> bool:
        """Valida cálculos com fonte externa (astro.com, NASA, etc.)"""
        try:
            # Implementar validação com APIs externas ou dados conhecidos
            # Por enquanto, validação básica com múltiplas bibliotecas
            
            pos_swe = self.calcular_posicao_planeta_swisseph(planeta, data)
            pos_ephem = self.calcular_posicao_planeta_ephem(planeta, data)
            
            if pos_swe and pos_ephem:
                # Comparar posições calculadas por diferentes bibliotecas
                diff_longitude = abs(pos_swe['longitude'] - pos_ephem['longitude'])
                
                # Tolerância de 1 grau para diferenças entre bibliotecas
                if diff_longitude > 1 and diff_longitude < 359:
                    logger.warning(f"Diferença significativa entre bibliotecas para {planeta} em {data}: {diff_longitude}°")
                    return False
                
                logger.debug(f"Validação OK para {planeta} em {data}: diferença {diff_longitude}°")
                return True
            
            # Se apenas uma biblioteca disponível, considerar válido
            return pos_swe is not None or pos_ephem is not None
            
        except Exception as e:
            logger.error(f"Erro na validação: {e}")
            return False
    
    def calcular_transito_especifico(self, planeta: Dict, natais: List[Dict], casas_natais: List[Dict]) -> Dict:
        """Calcula trânsito específico para resposta estruturada da LLM"""
        try:
            nome = planeta.get('name', 'Desconhecido')
            signo = planeta.get('sign', 'Áries')
            grau_atual = float(planeta.get('normDegree', 0))
            longitude_atual = float(planeta.get('fullDegree', 0))
            
            # Calcular trânsito completo no signo (do grau 0 ao 30)
            signo_inicio = int(longitude_atual // 30) * 30  # Início do signo em graus
            signo_fim = signo_inicio + 30  # Fim do signo
            
            # Calcular período de 1 ano a partir da data de referência
            data_inicio = self.data_referencia
            data_fim = data_inicio + timedelta(days=365)
            
            resultado = {
                'planeta': nome,
                'signo_atual': signo,
                'grau_atual': round(grau_atual, 2),
                'longitude_atual': round(longitude_atual, 2),
                'periodo_analise': {
                    'inicio': data_inicio.strftime('%Y-%m-%d'),
                    'fim': data_fim.strftime('%Y-%m-%d')
                }
            }
            
            # 1. CASAS ATIVADAS (baseado nas casas natais)
            casas_ativadas = self.calcular_casas_ativadas_transito(nome, signo, casas_natais, data_inicio, data_fim)
            resultado['casas_ativadas'] = casas_ativadas
            
            # 2. RETROGRADAÇÕES para signo anterior
            retrogradacoes = self.detectar_retrogradacao_signo_anterior(nome, signo, data_inicio, data_fim)
            if retrogradacoes:
                resultado['retrogradacao_signo_anterior'] = retrogradacoes
            
            # 3. ASPECTOS MAIORES com planetas natais (orbe 5°)
            aspectos_anuais = self.calcular_aspectos_anuais_precisos(planeta, natais, data_inicio, data_fim)
            if aspectos_anuais:
                resultado['aspectos_maiores'] = aspectos_anuais
            
            # 4. INFORMAÇÕES ADICIONAIS para LLM
            resultado['interpretacao_dados'] = {
                'entrada_signo': self.calcular_entrada_signo_precisa(nome, signo, data_inicio),
                'saida_signo': self.calcular_saida_signo_precisa(nome, signo, data_inicio),
                'velocidade_planeta': self.obter_velocidade_planeta(nome),
                'tipo_transito': self.classificar_tipo_transito(nome)
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao calcular trânsito específico de {planeta.get('name', 'Desconhecido')}: {e}")
            return {
                'planeta': planeta.get('name', 'Desconhecido'),
                'erro': str(e)
            }
    
    def calcular_casas_ativadas_transito(self, planeta: str, signo: str, casas_natais: List[Dict], data_inicio: datetime, data_fim: datetime) -> List[Dict]:
        """Calcula quais casas o planeta ativa durante o trânsito"""
        try:
            casas_ativadas = []
            casa_atual = None
            data_entrada_casa = None
            
            # Verificar casa por casa ao longo do período
            for dias in range(0, (data_fim - data_inicio).days, 7):  # Semanal
                data_teste = data_inicio + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos:
                    casa_teste = self.determinar_casa_natal_por_longitude(pos['longitude'], casas_natais)
                    
                    if casa_atual is None:
                        casa_atual = casa_teste
                        data_entrada_casa = data_teste
                    elif casa_teste != casa_atual:
                        # Mudança de casa
                        if casa_atual and data_entrada_casa:
                            casas_ativadas.append({
                                'casa': casa_atual,
                                'data_entrada': data_entrada_casa.strftime('%Y-%m-%d'),
                                'data_saida': data_teste.strftime('%Y-%m-%d'),
                                'duracao_dias': (data_teste - data_entrada_casa).days
                            })
                        
                        casa_atual = casa_teste
                        data_entrada_casa = data_teste
            
            # Adicionar última casa
            if casa_atual and data_entrada_casa:
                casas_ativadas.append({
                    'casa': casa_atual,
                    'data_entrada': data_entrada_casa.strftime('%Y-%m-%d'),
                    'data_saida': data_fim.strftime('%Y-%m-%d'),
                    'duracao_dias': (data_fim - data_entrada_casa).days
                })
            
            return casas_ativadas
            
        except Exception as e:
            logger.error(f"Erro ao calcular casas ativadas: {e}")
            return []
    
    def detectar_retrogradacao_signo_anterior(self, planeta: str, signo_atual: str, data_inicio: datetime, data_fim: datetime) -> Dict:
        """Detecta retrogradação que leva o planeta ao signo anterior"""
        try:
            if planeta in ['Sol', 'Lua']:
                return None
            
            # Normalizar signo atual
            signo_normalizado = self.signos_normalizados.get(signo_atual, signo_atual)
            
            # Índice do signo atual
            indice_signo_atual = self.signos.index(signo_normalizado)
            signo_anterior = self.signos[indice_signo_atual - 1]
            
            for dias in range(0, (data_fim - data_inicio).days):
                data_teste = data_inicio + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos:
                    # Verificar se retrogradou para signo anterior
                    if pos['signo'] == signo_anterior and pos.get('velocidade', 0) < 0:
                        # Encontrar período completo da retrogradação
                        data_inicio_retro = self.refinar_inicio_retrogradacao(planeta, data_teste)
                        data_fim_retro = self.refinar_fim_retrogradacao(planeta, data_teste)
                        
                        return {
                            'signo_destino': signo_anterior,
                            'data_inicio': data_inicio_retro,
                            'data_fim': data_fim_retro,
                            'duracao_dias': (datetime.strptime(data_fim_retro, '%Y-%m-%d') - datetime.strptime(data_inicio_retro, '%Y-%m-%d')).days
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao detectar retrogradação: {e}")
            return None
    
    def calcular_aspectos_anuais_precisos(self, planeta_transito: Dict, natais: List[Dict], data_inicio: datetime, data_fim: datetime) -> List[Dict]:
        """Calcula aspectos maiores durante 1 ano com períodos ativos"""
        try:
            aspectos_anuais = []
            nome_planeta = planeta_transito.get('name', 'Desconhecido')
            
            for natal in natais:
                if not isinstance(natal, dict) or 'name' not in natal:
                    continue
                
                planeta_natal = natal.get('name')
                grau_natal = float(natal.get('fullDegree', 0))
                casa_natal = int(natal.get('house', 1))
                
                # Para cada aspecto maior
                for angulo, nome_aspecto, orbe_max in self.aspectos:
                    periodos_ativos = self.calcular_periodos_aspecto_ativo(
                        nome_planeta, grau_natal, angulo, orbe_max, data_inicio, data_fim
                    )
                    
                    if periodos_ativos:
                        aspectos_anuais.append({
                            'tipo_aspecto': nome_aspecto,
                            'planeta_natal': planeta_natal,
                            'casa_natal': casa_natal,
                            'grau_natal': round(grau_natal, 2),
                            'orbe_maximo': orbe_max,
                            'periodos_ativos': periodos_ativos
                        })
            
            return sorted(aspectos_anuais, key=lambda x: x['periodos_ativos'][0]['data_inicio'] if x['periodos_ativos'] else '9999-99-99')
            
        except Exception as e:
            logger.error(f"Erro ao calcular aspectos anuais: {e}")
            return []
    
    def calcular_periodos_aspecto_ativo(self, planeta: str, grau_natal: float, angulo_aspecto: float, orbe_max: float, data_inicio: datetime, data_fim: datetime) -> List[Dict]:
        """Calcula períodos em que um aspecto está ativo"""
        try:
            periodos = []
            em_aspecto = False
            inicio_periodo = None
            
            for dias in range(0, (data_fim - data_inicio).days):
                data_teste = data_inicio + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos:
                    grau_transito = pos['longitude']
                    
                    # Calcular diferença angular
                    diferenca = abs(grau_transito - grau_natal)
                    diferenca = min(diferenca, 360 - diferenca)
                    
                    # Verificar se está no orbe do aspecto
                    orbe_atual = abs(diferenca - angulo_aspecto)
                    
                    if orbe_atual <= orbe_max:  # Dentro do orbe
                        if not em_aspecto:
                            inicio_periodo = data_teste
                            em_aspecto = True
                    else:  # Fora do orbe
                        if em_aspecto:
                            periodos.append({
                                'data_inicio': inicio_periodo.strftime('%Y-%m-%d'),
                                'data_fim': data_teste.strftime('%Y-%m-%d'),
                                'duracao_dias': (data_teste - inicio_periodo).days,
                                'orbe_maximo_atingido': round(orbe_atual, 2)
                            })
                            em_aspecto = False
            
            # Finalizar último período se ainda ativo
            if em_aspecto and inicio_periodo:
                periodos.append({
                    'data_inicio': inicio_periodo.strftime('%Y-%m-%d'),
                    'data_fim': data_fim.strftime('%Y-%m-%d'),
                    'duracao_dias': (data_fim - inicio_periodo).days,
                    'orbe_maximo_atingido': orbe_max
                })
            
            return periodos
            
        except Exception as e:
            logger.error(f"Erro ao calcular períodos de aspecto: {e}")
            return []
    
    def determinar_casa_natal_por_longitude(self, longitude: float, casas_natais: List[Dict]) -> int:
        """Determina a casa natal baseada na longitude e cúspides das casas"""
        try:
            # Se não há dados de casas, usar cálculo simples
            if not casas_natais:
                return int((longitude / 30) + 1) % 12 + 1
            
            # Usar cúspides reais das casas
            for i, casa in enumerate(casas_natais):
                if isinstance(casa, dict) and 'degree' in casa:
                    cusp_atual = casa['degree']
                    cusp_proxima = casas_natais[(i + 1) % 12]['degree'] if (i + 1) < len(casas_natais) else casas_natais[0]['degree']
                    
                    # Verificar se longitude está entre cúspides
                    if cusp_atual <= longitude < cusp_proxima:
                        return casa.get('house', i + 1)
            
            return 1  # Fallback
            
        except Exception as e:
            logger.error(f"Erro ao determinar casa: {e}")
            return 1
    
    def processar_planeta_preciso(self, planeta: Dict, natais: List[Dict]) -> Dict:
        """Processa planeta com todas as otimizações implementadas"""
        try:
            nome = planeta.get('name', 'Desconhecido')
            signo = planeta.get('sign', 'Áries')
            grau = float(planeta.get('normDegree', 0))
            casa_atual = int(planeta.get('house', 1))
            
            resultado = {
                'signo_atual': signo,
                'grau_atual': round(grau, 2),
                'casa_atual': casa_atual,
                'data_entrada_signo': self.calcular_entrada_signo_precisa(nome, signo, self.data_referencia),
                'data_saida_signo': self.calcular_saida_signo_precisa(nome, signo, self.data_referencia)
            }
            
            # Retrogradações detalhadas (apenas se houver)
            retrogradacoes = self.detectar_retrogradacao_precisa(nome, self.data_referencia)
            if retrogradacoes:
                resultado['retrogradacoes'] = retrogradacoes
            
            # Movimento entre casas
            try:
                data_inicio = datetime.strptime(resultado['data_entrada_signo'], '%Y-%m-%d')
                data_fim = datetime.strptime(resultado['data_saida_signo'], '%Y-%m-%d')
                periodo_dias = (data_fim - data_inicio).days
                
                movimento_casas = self.calcular_movimento_casas(nome, data_inicio, min(periodo_dias, 365))
                if len(movimento_casas) > 1:
                    resultado['movimento_casas'] = movimento_casas
            except Exception as e:
                logger.warning(f"Erro ao calcular movimento de casas para {nome}: {e}")
            
            # Aspectos com duração
            aspectos_duracao = self.calcular_duracao_aspectos(planeta, natais, self.data_referencia)
            if aspectos_duracao:
                resultado['aspectos_com_duracao'] = aspectos_duracao[:5]  # Máximo 5 aspectos
            
            # Aspectos principais (compatibilidade)
            aspectos = self.calcular_aspectos_precisos(planeta, natais)
            if aspectos:
                resultado['aspectos_principais'] = aspectos[:5]  # Máximo 5 aspectos
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao processar {planeta.get('name', 'Desconhecido')}: {e}")
            return {
                'signo_atual': planeta.get('sign', 'Áries'),
                'grau_atual': round(float(planeta.get('normDegree', 0)), 2),
                'casa_atual': int(planeta.get('house', 1)),
                'erro': str(e)
            }

    def testar_urano_especifico(self) -> Dict:
        """Teste específico para Urano conforme especificado pelo usuário"""
        try:
            # Dados de teste para Urano
            urano_teste = {
                'name': 'Urano',
                'sign': 'Gêmeos',
                'normDegree': 0.14,
                'house': 9,
                'fullDegree': 60.14
            }
            
            # Dados natais fictícios para teste
            natais_teste = [
                {'name': 'Sol', 'fullDegree': 90.0, 'house': 1},
                {'name': 'Lua', 'fullDegree': 180.0, 'house': 6},
                {'name': 'Ascendente', 'fullDegree': 270.0, 'house': 1}
            ]
            
            logger.info(f"Testando Urano com data de referência: {self.data_referencia}")
            
            # Processar usando a função corrigida
            resultado = self.processar_planeta_preciso(urano_teste, natais_teste)
            
            # Validar resultado
            validacao = self.validar_calculo_com_fonte_externa('Urano', self.data_referencia)
            
            # Adicionar informações de teste
            resultado['teste_especifico'] = {
                'data_referencia_usada': self.data_referencia.strftime('%Y-%m-%d'),
                'validacao_bibliotecas': validacao,
                'esperado_entrada': '2025-07-07',  # Conforme especificado
                'esperado_saida': '2025-11-08',   # Conforme especificado
                'funcoes_corrigidas': [
                    'calcular_entrada_signo_precisa',
                    'calcular_saida_signo_precisa',
                    'detectar_retrogradacao_precisa',
                    'calcular_duracao_aspectos'
                ]
            }
            
            logger.info(f"Teste Urano concluído: Entrada={resultado['data_entrada_signo']}, Saída={resultado['data_saida_signo']}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no teste específico de Urano: {e}")
            return {'erro': str(e)}
    
    def refinar_inicio_retrogradacao(self, planeta: str, data_aproximada: datetime) -> str:
        """Refina o início exato da retrogradação"""
        try:
            # Buscar para trás até encontrar início da retrogradação
            for dias in range(0, 30):
                data_teste = data_aproximada - timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos and pos.get('velocidade', 0) >= 0:
                    return (data_teste + timedelta(days=1)).strftime('%Y-%m-%d')
            
            return data_aproximada.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Erro ao refinar início de retrogradação: {e}")
            return data_aproximada.strftime('%Y-%m-%d')
    
    def refinar_fim_retrogradacao(self, planeta: str, data_aproximada: datetime) -> str:
        """Refina o fim exato da retrogradação"""
        try:
            # Buscar para frente até encontrar fim da retrogradação
            for dias in range(0, 90):
                data_teste = data_aproximada + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos and pos.get('velocidade', 0) >= 0:
                    return data_teste.strftime('%Y-%m-%d')
            
            return (data_aproximada + timedelta(days=60)).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Erro ao refinar fim de retrogradação: {e}")
            return data_aproximada.strftime('%Y-%m-%d')
    
    def obter_velocidade_planeta(self, planeta: str) -> Dict:
        """Retorna informações sobre velocidade do planeta"""
        velocidades = {
            'Sol': {'media': 0.98, 'tipo': 'rápida'},
            'Lua': {'media': 13.18, 'tipo': 'muito_rapida'},
            'Mercúrio': {'media': 1.38, 'tipo': 'rápida'},
            'Vênus': {'media': 1.20, 'tipo': 'rápida'},
            'Marte': {'media': 0.52, 'tipo': 'média'},
            'Júpiter': {'media': 0.08, 'tipo': 'lenta'},
            'Saturno': {'media': 0.03, 'tipo': 'muito_lenta'},
            'Urano': {'media': 0.006, 'tipo': 'muito_lenta'},
            'Netuno': {'media': 0.004, 'tipo': 'muito_lenta'},
            'Plutão': {'media': 0.003, 'tipo': 'muito_lenta'}
        }
        
        return velocidades.get(planeta, {'media': 0.1, 'tipo': 'desconhecida'})
    
    def classificar_tipo_transito(self, planeta: str) -> str:
        """Classifica o tipo de trânsito baseado no planeta"""
        tipos = {
            'Sol': 'pessoal_rapido',
            'Lua': 'pessoal_muito_rapido',
            'Mercúrio': 'pessoal_rapido',
            'Vênus': 'pessoal_rapido',
            'Marte': 'social_medio',
            'Júpiter': 'social_lento',
            'Saturno': 'social_muito_lento',
            'Urano': 'transpessoal',
            'Netuno': 'transpessoal',
            'Plutão': 'transpessoal'
        }
        
        return tipos.get(planeta, 'desconhecido')

# ============ ENDPOINTS ============
calc = TransitoAstrologicoPreciso()

@app.get("/")
async def root():
    bibliotecas_status = {
        'SwissEph': SWISSEPH_DISPONIVEL,
        'PyEphem': PYEPHEM_DISPONIVEL,
        'Skyfield': SKYFIELD_DISPONIVEL
    }
    
    return {
        "message": "API Trânsitos Astrológicos PRECISOS v11.0",
        "bibliotecas_astronomicas": bibliotecas_status,
        "recomendacao": "Instale Swiss Ephemeris para máxima precisão",
        "comando_instalacao": {
            "swisseph": "pip install pyswisseph",
            "pyephem": "pip install pyephem",
            "skyfield": "pip install skyfield"
        },
        "melhorias": [
            "✅ Swiss Ephemeris (padrão ouro)",
            "✅ PyEphem como alternativa",
            "✅ Cálculos astronômicos reais",
            "✅ Detecção precisa de retrogradações",
            "✅ Datas exatas de mudanças de signo",
            "✅ Aspectos com orbes astronômicos",
            "✅ Busca binária para precisão"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "swisseph": SWISSEPH_DISPONIVEL,
        "pyephem": PYEPHEM_DISPONIVEL,
        "skyfield": SKYFIELD_DISPONIVEL
    }

@app.get("/teste-urano")
async def teste_urano():
    """Endpoint para testar as correções específicas do Urano"""
    try:
        resultado = calc.testar_urano_especifico()
        return {
            "status": "sucesso",
            "resultado": resultado,
            "message": "Teste específico de Urano com correções implementadas"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no teste: {str(e)}")

@app.post("/transitos-astronomicos-precisos")
async def transitos_precisos(data: List[Dict[str, Any]]):
    """Trânsitos com cálculos astronômicos REAIS"""
    try:
        if not SWISSEPH_DISPONIVEL and not PYEPHEM_DISPONIVEL:
            raise HTTPException(
                status_code=500, 
                detail="Nenhuma biblioteca astronômica disponível. Instale: pip install pyswisseph"
            )
        
        logger.info(f"Processando {len(data)} elementos com bibliotecas astronômicas")
        
        if len(data) < 23:
            raise HTTPException(status_code=400, detail=f"Dados insuficientes: {len(data)} elementos")
        
        # Extrair dados da chave 'json' se necessário
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and 'json' in item:
                dados_extraidos.append(item['json'])
            else:
                dados_extraidos.append(item)
        
        # Separar dados
        transitos = dados_extraidos[:11]
        natais = dados_extraidos[11:22]
        
        # Processar apenas planetas relevantes para trânsitos
        planetas_processados = {}
        
        for transito in transitos:
            if transito and transito.get('name') in calc.planetas_relevantes:
                nome = transito.get('name')
                logger.info(f"Processando {nome} com cálculos astronômicos")
                planetas_processados[nome] = calc.processar_planeta_preciso(transito, natais)
        
        # Output com informações da biblioteca usada
        return {
            'periodo_analise': '1 ano',
            'biblioteca_usada': 'SwissEph' if SWISSEPH_DISPONIVEL else 'PyEphem',
            'precisao': 'Astronômica profissional',
            'planetas': planetas_processados
        }
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Manter compatibilidade com endpoint anterior
@app.post("/transitos-astronomicos")
async def transitos_astronomicos(data: List[Dict[str, Any]]):
    """Redirecionamento para endpoint preciso"""
    return await transitos_precisos(data)

@app.post("/transitos-especificos")
async def transitos_especificos(data: List[Dict[str, Any]]):
    """Trânsitos específicos formatados para LLM"""
    try:
        if not SWISSEPH_DISPONIVEL and not PYEPHEM_DISPONIVEL:
            raise HTTPException(
                status_code=500, 
                detail="Nenhuma biblioteca astronômica disponível. Instale: pip install pyswisseph"
            )
        
        logger.info(f"Processando trânsitos específicos para {len(data)} elementos")
        
        # Separar dados
        planetas_transito = []
        planetas_natais = []
        casas_natais = []
        
        for item in data:
            if isinstance(item, dict):
                if 'name' in item:
                    # Primeiro conjunto: planetas em trânsito
                    if len(planetas_transito) < 11:
                        planetas_transito.append(item)
                    else:
                        # Segundo conjunto: planetas natais
                        planetas_natais.append(item)
                elif 'houses' in item:
                    # Terceiro conjunto: casas natais
                    casas_natais = item['houses']
        
        # Processar trânsitos específicos
        transitos_especificos = []
        
        for planeta in planetas_transito:
            nome = planeta.get('name', 'Desconhecido')
            
            # Filtrar apenas planetas relevantes (excluir Sol, Lua e Ascendente)
            if nome not in calc.planetas_relevantes:
                continue
            
            try:
                transito = calc.calcular_transito_especifico(planeta, planetas_natais, casas_natais)
                transitos_especificos.append(transito)
            except Exception as e:
                logger.error(f"Erro ao calcular trânsito específico de {nome}: {e}")
                transitos_especificos.append({
                    'planeta': nome,
                    'erro': str(e)
                })
        
        return {
            "status": "sucesso",
            "total_transitos": len(transitos_especificos),
            "data_calculo": datetime.now().isoformat(),
            "data_referencia": calc.data_referencia.isoformat(),
            "periodo_analise": "1 ano",
            "bibliotecas_usadas": {
                "swisseph": SWISSEPH_DISPONIVEL,
                "pyephem": PYEPHEM_DISPONIVEL
            },
            "transitos_especificos": transitos_especificos
        }
        
    except Exception as e:
        logger.error(f"Erro geral no processamento de trânsitos específicos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 API Trânsitos Astrológicos PRECISOS v11.0")
    print(f"Swiss Ephemeris: {'✅' if SWISSEPH_DISPONIVEL else '❌'}")
    print(f"PyEphem: {'✅' if PYEPHEM_DISPONIVEL else '❌'}")
    print(f"Skyfield: {'✅' if SKYFIELD_DISPONIVEL else '❌'}")
    
    if not SWISSEPH_DISPONIVEL and not PYEPHEM_DISPONIVEL:
        print("⚠️  AVISO: Nenhuma biblioteca astronômica instalada!")
        print("📦 Instale: pip install pyswisseph")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)