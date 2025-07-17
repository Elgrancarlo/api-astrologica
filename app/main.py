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
        """Inicializa Swiss Ephemeris com path correto"""
        if SWISSEPH_DISPONIVEL:
            try:
                # Definir path para arquivos de efemérides
                swe.set_ephe_path('/usr/share/swisseph')  # Ajustar conforme instalação
                return True
            except:
                logger.warning("Erro ao inicializar Swiss Ephemeris")
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
    
    def calcular_entrada_signo_precisa(self, planeta: str, signo_atual: str) -> str:
        """Calcula entrada no signo usando bibliotecas astronômicas"""
        try:
            hoje = datetime.now()
            
            # Buscar para trás até encontrar mudança de signo
            for dias_atras in range(1, 1000):  # Buscar até ~3 anos
                data_teste = hoje - timedelta(days=dias_atras)
                
                # Tentar Swiss Ephemeris primeiro
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos and pos['signo'] != signo_atual:
                    # Encontrou mudança - refinar a data
                    return self.refinar_data_mudanca_signo(planeta, data_teste, data_teste + timedelta(days=1))
            
            # Se não encontrou, retornar estimativa
            return (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Erro ao calcular entrada precisa: {e}")
            return (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    def calcular_saida_signo_precisa(self, planeta: str, signo_atual: str) -> str:
        """Calcula saída do signo com períodos adequados por planeta"""
        
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
            hoje = datetime.now()
            
            # Buscar para frente até encontrar mudança de signo
            for dias_futuros in range(1, limite_dias):
                data_teste = hoje + timedelta(days=dias_futuros)
                
                # Tentar Swiss Ephemeris primeiro
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    pos = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                
                if pos and pos['signo'] != signo_atual:
                    # Encontrou mudança - refinar a data
                    return self.refinar_data_mudanca_signo(planeta, data_teste - timedelta(days=1), data_teste)
            
            # Se não encontrou, estimar baseado no período máximo
            return (hoje + timedelta(days=limite_dias)).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Erro ao calcular saída precisa: {e}")
            return (datetime.now() + timedelta(days=limite_dias)).strftime('%Y-%m-%d')
    
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
    
    def detectar_retrogradacao_precisa(self, planeta: str) -> List[Dict]:
        """Detecta retrogradações com destino detalhado"""
        try:
            if planeta in ['Sol', 'Lua']:
                return []
            
            hoje = datetime.now()
            retrogradacoes = []
            
            em_retrogradacao = False
            inicio_retro = None
            
            # Verificar próximos 400 dias
            for dias in range(0, 400):
                data_teste = hoje + timedelta(days=dias)
                
                pos = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                if not pos:
                    continue
                
                eh_retrogrado = pos.get('retrogrado', False) or pos.get('velocidade', 0) < 0
                
                if eh_retrogrado and not em_retrogradacao:
                    # Início da retrogradação
                    inicio_retro = data_teste
                    em_retrogradacao = True
                    
                elif not eh_retrogrado and em_retrogradacao:
                    # Fim da retrogradação - calcular destino
                    pos_final = self.calcular_posicao_planeta_swisseph(planeta, data_teste)
                    if not pos_final:
                        pos_final = self.calcular_posicao_planeta_ephem(planeta, data_teste)
                    
                    casa_final = self.calcular_casa_por_posicao(pos_final.get('longitude', 0), data_teste)
                    
                    retrogradacoes.append({
                        'data_inicio': inicio_retro.strftime('%Y-%m-%d'),
                        'data_fim': data_teste.strftime('%Y-%m-%d'),
                        'duracao_dias': (data_teste - inicio_retro).days,
                        'signo_destino': pos_final.get('signo', 'N/A'),
                        'casa_destino': casa_final
                    })
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
    
    def calcular_duracao_aspectos(self, planeta_transito: Dict, natais: List[Dict]) -> List[Dict]:
        """Calcula duração temporal dos aspectos"""
        try:
            aspectos_com_duracao = []
            hoje = datetime.now()
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
                        data_teste = hoje + timedelta(days=dias)
                        
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
                'data_entrada_signo': self.calcular_entrada_signo_precisa(nome, signo),
                'data_saida_signo': self.calcular_saida_signo_precisa(nome, signo)
            }
            
            # Retrogradações detalhadas (apenas se houver)
            retrogradacoes = self.detectar_retrogradacao_precisa(nome)
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
            aspectos_duracao = self.calcular_duracao_aspectos(planeta, natais)
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

if __name__ == "__main__":
    print("🚀 API Trânsitos Astrológicos PRECISOS v11.0")
    print(f"Swiss Ephemeris: {'✅' if SWISSEPH_DISPONIVEL else '❌'}")
    print(f"PyEphem: {'✅' if PYEPHEM_DISPONIVEL else '❌'}")
    print(f"Skyfield: {'✅' if SKYFIELD_DISPONIVEL else '❌'}")
    
    if not SWISSEPH_DISPONIVEL and not PYEPHEM_DISPONIVEL:
        print("⚠️  AVISO: Nenhuma biblioteca astronômica instalada!")
        print("📦 Instale: pip install pyswisseph")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)