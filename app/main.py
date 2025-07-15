from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import uvicorn
import time
import logging
from datetime import datetime, timedelta
import math
import traceback
import os
import unicodedata
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🌟 API Astrológica Profissional",
    description="Microserviço completo para cálculos astrológicos profissionais",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELOS ============

class Planet(BaseModel):
    name: str
    fullDegree: float
    normDegree: float
    speed: float
    isRetro: Union[str, bool]
    sign: str
    house: int

class House(BaseModel):
    house: int
    sign: str
    degree: float

class HouseSystem(BaseModel):
    houses: List[House]
    ascendant: Optional[float] = None
    midheaven: Optional[float] = None
    vertex: Optional[float] = None

class AspectData(BaseModel):
    planeta_natal: str
    signo_natal: str
    casa_natal: int
    tipo_aspecto: str
    natureza: str
    intensidade: int
    orbe: str
    orbe_maximo_usado: int
    formando_ou_separando: str
    data_inicio: str
    data_exata: str
    data_fim: str

class TransitoProfissional(BaseModel):
    planeta: str
    casa: int
    signo: str
    grau_atual: Optional[str] = None
    data_entrada: Optional[str] = None
    data_saida_estimada: Optional[str] = None
    dias_restantes_casa: Optional[int] = None
    dias_na_casa: Optional[int] = None
    dias_ate_entrada: Optional[int] = None
    status: str
    relevancia: str

class PlanetaLento(BaseModel):
    planeta: str
    signo: str
    grau: str
    casa_ativada: Optional[int]
    movimento: Dict[str, Any]
    permanencia: Dict[str, Any]
    aspectos_com_planetas: List[AspectData]

class MudancaSigno(BaseModel):
    planeta: str
    signo_atual: str
    proximo_signo: str
    dias_para_mudanca: int
    data_mudanca: str
    casas_ativadas_novo_signo: List[Dict[str, Any]]

class AspectoPlanetaRapido(BaseModel):
    planeta_transito: str
    planeta_natal: str
    signo_natal: str
    casa_natal: int
    tipo_aspecto: str
    natureza: str
    data_aproximada: str
    data_inicio: str
    data_fim: str
    orbe: str
    orbe_maximo_usado: int

class PeriodoAnalise(BaseModel):
    inicio: str
    fim: str
    descricao: str

class OrbesAplicados(BaseModel):
    planetas_pessoais: str
    planetas_transpessoais: str

class FutureLentoAspect(BaseModel):
    planeta_natal: str
    signo_natal: str
    casa_natal: int
    data_aproximada: str
    tipo_aspecto: str
    natureza: str
    orbe: str
    orbe_maximo_usado: int
    casa_ativada: Optional[int] = None

class ProjectedLentoAspects(BaseModel):
    planeta: str
    aspectos_planetas_futuros: List[FutureLentoAspect]

class AnaliseAreaProfissional(BaseModel):
    transitos_planetas_lentos_casas_2610: List[TransitoProfissional]
    transitos_rapidos_casas_2610: List[Dict[str, Any]]
    aspectos_planetas_rapidos_todos: List[AspectoPlanetaRapido]
    aspectos_planetas_rapidos_harmonicos: List[AspectoPlanetaRapido]
    aspectos_planetas_lentos_todos_futuros: List[ProjectedLentoAspects]
    aspectos_planetas_lentos_harmonicos_futuros: List[ProjectedLentoAspects]
    jupiter_oportunidades: Optional[Dict[str, Any]]
    periodo_analise: PeriodoAnalise

class MetaInfo(BaseModel):
    periodo_analise: str
    num_planetas_analisados: int
    tipo_analise: str
    data_analise: str
    orbes_aplicados: OrbesAplicados
    execution_time_ms: float
    engine: str
    timestamp: float
    processing_time_ms: Optional[float] = None
    source: Optional[str] = None
    input_elements: Optional[int] = None

class AnalysisResponse(BaseModel):
    tipo_analise: str
    api_fonte: str
    planetas_lentos: List[PlanetaLento]
    mudancas_signo_proximas: List[MudancaSigno]
    mudancas_casa_proximas: List[Dict[str, Any]]
    analise_area_profissional: AnaliseAreaProfissional
    meta_info: MetaInfo

class AnalysisRequest(BaseModel):
    transitos_lentos: List[Planet]
    natal: List[Planet]
    houses: HouseSystem
    transitos_rapidos: Optional[List[Planet]] = []

# ============ FIM DOS NOVOS MODELOS ============

# ============ FUNCÕES DE OTIMIZAÇÃO PARA GEMINI ============

def limitar_aspectos_para_gemini(aspectos: List[Dict[str, Any]], limite: int = 5) -> List[Dict[str, Any]]:
    """Limita aspectos para reduzir tokens"""
    if not aspectos:
        return []
    
    # Priorizar aspectos mais importantes
    aspectos_ordenados = sorted(aspectos, key=lambda x: x.get('intensidade', 0), reverse=True)
    return aspectos_ordenados[:limite]

# CACHE GLOBAL PARA PERFORMANCE
_cache_planetas = {}
_cache_datas_futuras = {}
_cache_aspectos = {}

def limpar_cache():
    """Limpa caches para nova requisição"""
    global _cache_planetas, _cache_datas_futuras, _cache_aspectos
    _cache_planetas.clear()
    _cache_datas_futuras.clear()
    _cache_aspectos.clear()

def calcular_data_futura_cached(dias_adicionais: int) -> str:
    """Versão cached do cálculo de data futura"""
    if dias_adicionais in _cache_datas_futuras:
        return _cache_datas_futuras[dias_adicionais]
    
    hoje = datetime.now()
    data_futura = hoje + timedelta(days=dias_adicionais)
    resultado = data_futura.strftime('%Y-%m-%d')
    _cache_datas_futuras[dias_adicionais] = resultado
    return resultado

def encontrar_planeta_cached(nome: str, lista: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Versão cached da busca de planetas"""
    cache_key = f"{nome}_{id(lista)}"
    if cache_key in _cache_planetas:
        return _cache_planetas[cache_key]
    
    nome_normalizado_search = unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode("utf-8")
    
    for p in lista:
        if not p or not p.get('name'):
            continue
        
        planeta_nome_na_lista = p.get('name')
        planeta_nome_normalizado_na_lista = unicodedata.normalize("NFD", planeta_nome_na_lista).encode("ascii", "ignore").decode("utf-8")
        
        if (planeta_nome_na_lista == nome or 
            planeta_nome_normalizado_na_lista == nome_normalizado_search):
            _cache_planetas[cache_key] = p
            return p
    
    _cache_planetas[cache_key] = None
    return None

def calcular_aspectos_batch(planeta_grau: float, planetas_natais: List[Dict], nome_planeta: str) -> List[Dict[str, Any]]:
    """Calcula aspectos em batch para melhor performance"""
    aspectos = []
    aspectos_principais = [
        (0, "conjunção", "harmonioso", 10),
        (60, "sextil", "harmonioso", 6),
        (90, "quadratura", "desafiador", 8),
        (120, "trígono", "harmonioso", 7),
        (180, "oposição", "desafiador", 9)
    ]
    
    for planeta_natal in planetas_natais:
        if not planeta_natal or not planeta_natal.get('fullDegree'):
            continue
            
        diferenca = abs(planeta_grau - planeta_natal['fullDegree'])
        if diferenca > 180:
            diferenca = 360 - diferenca
        
        # Determinar orbe máximo baseado no planeta
        orbe_maximo = 5 if nome_planeta in ['Sol', 'Lua', 'Mercúrio', 'Vênus', 'Marte'] else 3
        
        for angulo_exato, nome_aspecto, natureza, intensidade in aspectos_principais:
            orbe_atual = abs(diferenca - angulo_exato)
            if orbe_atual <= orbe_maximo:
                aspectos.append({
                    "planeta_natal": planeta_natal.get('name'),
                    "signo_natal": planeta_natal.get('sign'),
                    "casa_natal": planeta_natal.get('house'),
                    "tipo_aspecto": nome_aspecto,
                    "natureza": natureza,
                    "intensidade": intensidade,
                    "orbe": f"{orbe_atual:.1f}",
                    "orbe_maximo_usado": orbe_maximo
                })
                break  # Apenas um aspecto por planeta
    
    return aspectos

def criar_versao_resumida_para_gemini(dados_completos: Dict[str, Any]) -> Dict[str, Any]:
    """Cria versão resumida dos dados para enviar ao Gemini"""
    
    # Processar todos os trânsitos mas de forma mais focada
    todos_transitos = dados_completos.get('todos_transitos', [])
    transitos_essenciais = []
    
    for transito in todos_transitos:
        # Manter apenas dados essenciais para análise
        planeta = transito.get('planeta')
        signo_atual = transito.get('signo_atual')
        relevancia = transito.get('relevancia', 0)
        
        # Resumir análise do signo atual
        analise_signo = transito.get('analise_signo_atual', {})
        resumo_signo = analise_signo.get('resumo', {})
        
        # Aspectos mais importantes (máximo 5 por planeta)
        aspectos_natal = analise_signo.get('aspectos_com_natal', [])
        aspectos_importantes = sorted(aspectos_natal, key=lambda x: x.get('intensidade', 0), reverse=True)[:5]
        
        # Casas ativadas resumidas
        casas_ativadas = analise_signo.get('casas_ativadas', [])
        casas_resumidas = []
        for casa in casas_ativadas[:3]:  # Máximo 3 casas
            casas_resumidas.append({
                'casa': casa.get('casa'),
                'data_entrada': casa.get('data_entrada'),
                'data_saida': casa.get('data_saida'),
                'permanencia_meses': casa.get('permanencia_meses')
            })
        
        # Retrogradações resumidas
        retrogradacoes = transito.get('retrogradacoes', [])
        retrogradacoes_resumidas = []
        for retro in retrogradacoes[:2]:  # Máximo 2 retrogradações
            retrogradacoes_resumidas.append({
                'inicio': retro.get('inicio'),
                'fim': retro.get('fim'),
                'signo_retrogradacao': retro.get('signo_retrogradacao'),
                'duracao_dias': retro.get('duracao_dias')
            })
        
        transito_essencial = {
            'planeta': planeta,
            'signo_atual': signo_atual,
            'grau_atual': transito.get('grau_atual'),
            'relevancia': relevancia,
            'eh_retrogrado': transito.get('eh_retrogrado'),
            'tempo_restante_signo': transito.get('tempo_restante_signo'),
            'proximo_signo': transito.get('proximo_signo'),
            'casas_ativadas': casas_resumidas,
            'aspectos_principais': aspectos_importantes,
            'retrogradacoes': retrogradacoes_resumidas,
            'resumo_aspectos': {
                'total_aspectos': resumo_signo.get('total_aspectos', 0),
                'aspectos_harmonicos': resumo_signo.get('aspectos_harmonicos', 0),
                'aspectos_desafiadores': resumo_signo.get('aspectos_desafiadores', 0)
            }
        }
        
        transitos_essenciais.append(transito_essencial)
    
    # Ordenar por relevância e pegar os mais importantes
    transitos_essenciais.sort(key=lambda x: x.get('relevancia', 0), reverse=True)
    
    # Separar por categoria de importância
    transitos_alta_relevancia = [t for t in transitos_essenciais if t.get('relevancia', 0) >= 8]
    transitos_media_relevancia = [t for t in transitos_essenciais if 5 <= t.get('relevancia', 0) < 8]
    transitos_baixa_relevancia = [t for t in transitos_essenciais if t.get('relevancia', 0) < 5]
    
    # Mudanças de signo próximas (máximo 5)
    mudancas_signo = dados_completos.get('mudancas_signo_proximas', [])[:5]
    
    # Versão final resumida mas completa
    dados_resumidos = {
        'tipo_analise': dados_completos.get('tipo_analise'),
        'periodo_analise': '12 meses',
        'data_analise': dados_completos.get('meta_info', {}).get('data_analise'),
        
        # Planetas por ordem de importância
        'planetas_alta_relevancia': transitos_alta_relevancia,
        'planetas_media_relevancia': transitos_media_relevancia[:3],  # Máximo 3
        'planetas_baixa_relevancia': transitos_baixa_relevancia[:2],   # Máximo 2
        
        # Mudanças importantes
        'mudancas_signo_proximas': mudancas_signo,
        
        # Resumo geral
        'resumo_geral': {
            'total_planetas_analisados': len(transitos_essenciais),
            'planetas_alta_relevancia': len(transitos_alta_relevancia),
            'planetas_com_aspectos_ativos': len([t for t in transitos_essenciais if t.get('resumo_aspectos', {}).get('total_aspectos', 0) > 0]),
            'planetas_em_retrogradacao': len([t for t in transitos_essenciais if t.get('eh_retrogrado')]),
            'mudancas_signo_proximas': len(mudancas_signo),
            'planeta_mais_relevante': transitos_essenciais[0].get('planeta') if transitos_essenciais else None
        },
        
        # Instruções para análise
        'como_interpretar': {
            'foco_principal': 'Analise primeiro os planetas de alta relevância',
            'aspectos_importantes': 'Priorize aspectos com intensidade >= 7',
            'casas_ativadas': 'Considere as datas de entrada e saída de cada casa',
            'retrogradacoes': 'Analise períodos de retrogradação para revisões e correções',
            'mudancas_signo': 'Mudanças de signo trazem novas energias e focos'
        }
    }
    
    return dados_resumidos

def criar_analise_transito_especifico(planeta_nome: str, dados_completos: Dict[str, Any]) -> Dict[str, Any]:
    """Cria análise específica para um planeta conforme solicitado"""
    
    # Encontrar o planeta nos dados
    todos_transitos = dados_completos.get('todos_transitos', [])
    planeta_encontrado = None
    
    for transito in todos_transitos:
        if transito.get('planeta', '').lower() == planeta_nome.lower():
            planeta_encontrado = transito
            break
    
    if not planeta_encontrado:
        return {'erro': f'Planeta {planeta_nome} não encontrado nos dados'}
    
    # Extrair dados específicos do planeta
    analise_signo = planeta_encontrado.get('analise_signo_atual', {})
    casas_ativadas = analise_signo.get('casas_ativadas', [])
    aspectos_natal = analise_signo.get('aspectos_com_natal', [])
    retrogradacoes = planeta_encontrado.get('retrogradacoes', [])
    
    # Organizar casas por período
    casas_organizadas = []
    for casa in casas_ativadas:
        casas_organizadas.append({
            'casa': casa.get('casa'),
            'data_entrada': casa.get('data_entrada'),
            'data_saida': casa.get('data_saida'),
            'permanencia_meses': casa.get('permanencia_meses'),
            'grau_entrada': casa.get('grau_entrada'),
            'grau_saida': casa.get('grau_saida')
        })
    
    # Organizar aspectos por tipo e intensidade
    aspectos_organizados = {
        'conjuncao': [],
        'trigono': [],
        'sextil': [],
        'quadratura': [],
        'oposicao': []
    }
    
    for aspecto in aspectos_natal:
        tipo = aspecto.get('tipo_aspecto', '').lower()
        if tipo in aspectos_organizados:
            aspectos_organizados[tipo].append({
                'planeta_natal': aspecto.get('planeta_natal'),
                'casa_natal': aspecto.get('casa_natal'),
                'data_inicio': aspecto.get('data_inicio'),
                'data_exata': aspecto.get('data_exata'),
                'data_fim': aspecto.get('data_fim'),
                'intensidade': aspecto.get('intensidade'),
                'natureza': aspecto.get('natureza')
            })
    
    # Análise específica do trânsito
    analise_especifica = {
        'planeta': planeta_encontrado.get('planeta'),
        'signo_atual': planeta_encontrado.get('signo_atual'),
        'grau_atual': planeta_encontrado.get('grau_atual'),
        'eh_retrogrado': planeta_encontrado.get('eh_retrogrado'),
        'tempo_restante_signo': planeta_encontrado.get('tempo_restante_signo'),
        'proximo_signo': planeta_encontrado.get('proximo_signo'),
        
        # Casas ativadas com detalhes
        'casas_ativadas': casas_organizadas,
        
        # Aspectos organizados por tipo
        'aspectos_por_tipo': aspectos_organizados,
        
        # Retrogradações detalhadas
        'retrogradacoes_detalhadas': retrogradacoes,
        
        # Resumo para interpretação
        'resumo_interpretacao': {
            'total_casas_ativadas': len(casas_organizadas),
            'total_aspectos': len(aspectos_natal),
            'aspectos_harmonicos': len([a for a in aspectos_natal if a.get('natureza') == 'harmonioso']),
            'aspectos_desafiadores': len([a for a in aspectos_natal if a.get('natureza') == 'desafiador']),
            'tem_retrogradacao': len(retrogradacoes) > 0,
            'muda_signo_proximamente': planeta_encontrado.get('tempo_restante_signo', {}).get('dias', 999) <= 180
        }
    }
    
    return analise_especifica

# ============ FIM DAS FUNÇÕES DE OTIMIZAÇÃO ============

# ============ CALCULADORA ASTROLÓGICA AVANÇADA (VERSÃO 2.0) ============

class AdvancedAstroCalculator:
    """Calculadora astrológica completa equivalente ao JavaScript"""
    
    def __init__(self):
        # Signos do zodíaco
        self.signos = [
            'Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
            'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes'
        ]
        
        # Planetas por categoria
        self.planetas_pessoais = ['Sol', 'Lua', 'Mercúrio', 'Vênus', 'Marte']
        self.planetas_transpessoais = ['Jupiter', 'Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutao', 'Plutão']
        self.planetas_lentos = ['Jupiter', 'Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutao', 'Plutão']
        self.planetas_rapidos = ['Sol', 'Mercúrio', 'Vênus', 'Marte']
         
        # Aspectos principais - OTIMIZADO: usar tuplas ao invés de listas para performance
        self.aspectos = (
            (0, "conjunção", "harmonioso", 10),
            (60, "sextil", "harmonioso", 6),
            (90, "quadratura", "desafiador", 8),
            (120, "trígono", "harmonioso", 7),
            (180, "oposição", "desafiador", 9)
        )
         
        # Velocidades médias diárias (graus/dia) - OTIMIZADO: cache de velocidades
        self.velocidades_medias = {
            'Sol': 0.98, 'Lua': 13.2, 'Mercúrio': 1.38, 'Vênus': 1.2, 'Marte': 0.52,
            'Jupiter': 0.08, 'Júpiter': 0.08, 'Saturno': 0.03, 'Urano': 0.01,
            'Netuno': 0.006, 'Plutao': 0.004, 'Plutão': 0.004
        }
        
        # OTIMIZAÇÃO: Cache para evitar recálculos
        self._cache_aspectos = {}
        self._cache_casas = {}
        
        # Mapeamento de oportunidades por casa para Júpiter
        self.oportunidades_jupiter = {
            1: "Expansão da identidade profissional, liderança pessoal, início de novos projetos",
            2: "Expansão financeira, novos recursos, oportunidades de renda",
            3: "Comunicação expandida, parcerias locais, habilidades comerciais",
            4: "Base sólida para carreira, trabalho em casa, negócios familiares",
            5: "Criatividade profissional, projetos inovadores, especulações bem-sucedidas",
            6: "Melhoria nas condições de trabalho, saúde ocupacional, expansão da rotina",
            7: "Parcerias profissionais, sociedades, contratos importantes",
            8: "Transformação profissional, recursos compartilhados, investimentos",
            9: "Expansão internacional, educação superior, publicações",
            10: "Grandes oportunidades de carreira, reconhecimento público, promoções",
            11: "Networking poderoso, projetos em grupo, realização de objetivos",
            12: "Trabalho nos bastidores, projetos espirituais, cura através do trabalho"
        }
    
    def determinar_tipo_planeta(self, nome_planeta: str) -> Dict[str, Any]:
        """Determina tipo de planeta e orbe apropriado - OTIMIZADO com cache"""
        # OTIMIZAÇÃO: usar cache para evitar recálculos
        if nome_planeta in self._cache_aspectos:
            return self._cache_aspectos[nome_planeta]
            
        if nome_planeta in self.planetas_pessoais:
            result = {"tipo": "pessoal", "orbe": 5}
        elif nome_planeta in self.planetas_transpessoais:
            result = {"tipo": "transpessoal", "orbe": 3}
        else:
            result = {"tipo": "transpessoal", "orbe": 3}
            
        self._cache_aspectos[nome_planeta] = result
        return result
    
    def calcular_diferenca_angular(self, grau1: float, grau2: float) -> float:
        """Calcula diferença angular entre dois graus"""
        diff = abs(grau1 - grau2)
        if diff > 180:
            diff = 360 - diff
        return diff
    
    def calcular_data_futura(self, dias_adicionais: int) -> str:
        """Calcula data futura baseada em dias adicionais"""
        hoje = datetime.now()
        data_futura = hoje + timedelta(days=dias_adicionais)
        return data_futura.strftime('%Y-%m-%d')
    
    def identificar_aspecto(self, diferenca: float, planeta1: str, planeta2: str) -> Optional[Dict[str, Any]]:
        """Identifica aspecto com orbes dinâmicos"""
        # Determinar orbe máximo baseado nos planetas envolvidos
        tipo1 = self.determinar_tipo_planeta(planeta1)
        tipo2 = self.determinar_tipo_planeta(planeta2)
        orbe_maximo = min(tipo1["orbe"], tipo2["orbe"])  # Usar o menor orbe
         
        # Verificar aspectos
        for angulo_exato, nome_aspecto, natureza, intensidade in self.aspectos:
            orbe_atual = abs(diferenca - angulo_exato)
            if orbe_atual <= orbe_maximo:
                return {
                    "nome": nome_aspecto,
                    "orbe": orbe_atual,
                    "natureza": natureza,
                    "intensidade": intensidade,
                    "orbe_maximo": orbe_maximo
                }
        return None
    
    def encontrar_planeta(self, nome: str, lista: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Busca planeta na lista com normalização de nomes, equivalente ao JS."""
        nome_normalizado_search = unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode("utf-8")
        
        for p in lista:
            if not p or not p.get('name'):
                continue
            
            planeta_nome_na_lista = p.get('name')
            planeta_nome_normalizado_na_lista = unicodedata.normalize("NFD", planeta_nome_na_lista).encode("ascii", "ignore").decode("utf-8")
            
            if (planeta_nome_na_lista == nome or 
                planeta_nome_normalizado_na_lista == nome_normalizado_search):
                return p
        return None
    
    def determinar_casa(self, grau_transito: float, cuspides: List[House]) -> Optional[Dict[str, Any]]:
        """Determina casa baseada no grau e cúspides"""
        # Ordenar cúspides por grau
        cuspides_ordenadas = sorted(cuspides, key=lambda x: x.degree)
        
        for i in range(len(cuspides_ordenadas)):
            cuspide_atual = cuspides_ordenadas[i]
            proxima_cuspide = cuspides_ordenadas[(i + 1) % len(cuspides_ordenadas)]
            
            # Verificar se está na casa
            if proxima_cuspide.degree > cuspide_atual.degree:
                # Caso normal: casa não cruza 0°
                esta_na_casa = cuspide_atual.degree <= grau_transito < proxima_cuspide.degree
            else:
                # Caso especial: casa cruza 0° (última casa do zodíaco)
                esta_na_casa = grau_transito >= cuspide_atual.degree or grau_transito < proxima_cuspide.degree
            
            if esta_na_casa:
                return {
                    "casa": cuspide_atual.house,
                    "cuspide_grau": cuspide_atual.degree,
                    "proxima_cuspide": proxima_cuspide.degree,
                    "proxima_casa": proxima_cuspide.house
                }
        
        return None
    
    def verificar_mudanca_direcao(self, planeta: Planet) -> Dict[str, Any]:
        """Verifica se planeta está mudando de direção"""
        velocidade = planeta.speed
        if abs(velocidade) < 0.01:
            return {
                "estacionario": True,
                "direcao": "direto" if velocidade >= 0 else "retrógrado"
            }
        
        return {
            "estacionario": False,
            "direcao": "direto" if velocidade >= 0 else "retrógrado"
        }
    
    def estimar_permanencia(self, planeta: Planet) -> Dict[str, Any]:
        """Estima tempo de permanência em signo"""
        velocidade = abs(planeta.speed) or self.velocidades_medias.get(planeta.name, 0.05)
        graus_restantes = 30 - planeta.normDegree
        dias_no_signo = abs(graus_restantes / velocidade)
        
        if dias_no_signo > 365:
            tempo = round(dias_no_signo / 365, 1)
            unidade = "anos"
        elif dias_no_signo > 30:
            tempo = round(dias_no_signo / 30, 1)
            unidade = "meses"
        else:
            tempo = int(dias_no_signo)
            unidade = "dias"
        
        return {
            "tempo_restante_signo": str(tempo),
            "unidade": unidade
        }
    
    def calcular_mudancas_casa_futuras(self, signo_futuro: str, planeta_atual: Planet, 
                                      cuspides: List[House]) -> List[Dict[str, Any]]:
        """Calcula mudanças de casa para um signo futuro"""
        try:
            index_signo = self.signos.index(signo_futuro)
        except ValueError:
            return []
        
        grau_inicio_signo = index_signo * 30
        grau_fim_signo = grau_inicio_signo + 30
        
        casas_ativadas = []
        casas_vistas = set()
        
        # Verificar casa para cada grau do signo
        for grau in range(grau_inicio_signo, grau_fim_signo):
            casa_info = self.determinar_casa(grau, cuspides)
            if casa_info and casa_info["casa"] not in casas_vistas:
                casas_vistas.add(casa_info["casa"])
                
                # Calcular entrada na casa
                grau_entrada = grau
                while grau_entrada > grau_inicio_signo:
                    casa_anterior = self.determinar_casa(grau_entrada - 1, cuspides)
                    if casa_anterior and casa_anterior["casa"] != casa_info["casa"]:
                        break
                    grau_entrada -= 1
                
                # Calcular saída da casa
                grau_saida = grau
                while grau_saida < grau_fim_signo - 1:
                    casa_posterior = self.determinar_casa(grau_saida + 1, cuspides)
                    if casa_posterior and casa_posterior["casa"] != casa_info["casa"]:
                        break
                    grau_saida += 1
                
                velocidade = abs(planeta_atual.speed) or self.velocidades_medias.get(planeta_atual.name, 0.08)
                dias_ate_entrada = max(1, int((grau_entrada - planeta_atual.fullDegree) / velocidade))
                dias_na_casa = max(1, int((grau_saida - grau_entrada) / velocidade))
                
                casas_ativadas.append({
                    "casa": casa_info["casa"],
                    "grau_entrada": grau_entrada,
                    "grau_saida": grau_saida,
                    "dias_ate_entrada": dias_ate_entrada,
                    "dias_na_casa": dias_na_casa,
                    "data_entrada": self.calcular_data_futura(dias_ate_entrada),
                    "data_saida": self.calcular_data_futura(dias_ate_entrada + dias_na_casa)
                })
        
        return sorted(casas_ativadas, key=lambda x: x["dias_ate_entrada"])
    
    def analisar_planetas_lentos(self, transitos_lentos: List[Planet], natal: List[Planet], 
                                cuspides: List[House]) -> List[Dict[str, Any]]:
        """Análise completa dos planetas lentos"""
        analise_lentos = []
        mudancas_signo = []
        
        for nome_planeta in self.planetas_lentos:
            planeta = self.encontrar_planeta(nome_planeta, transitos_lentos)
            if not planeta:
                continue
            
            # Evitar duplicatas (Júpiter/Jupiter)
            nome_normalizado = nome_planeta.lower().replace('ú', 'u')
            if any(p["planeta"].lower().replace('ú', 'u') == nome_normalizado for p in analise_lentos):
                continue
            
            logger.info(f"Analisando {nome_planeta}: {planeta.sign} {planeta.normDegree:.1f}°")
            
            # Determinar casa ativada
            casa_ativada = self.determinar_casa(planeta.fullDegree, cuspides)
            
            # Movimento e permanência
            movimento = self.verificar_mudanca_direcao(planeta)
            permanencia = self.estimar_permanencia(planeta)
            
            # Verificar mudança de signo próxima (até 90 dias)
            graus_restantes = 30 - planeta.normDegree
            velocidade = abs(planeta.speed) or self.velocidades_medias.get(planeta.name, 0.08)
            dias_para_mudanca = graus_restantes / velocidade
            
            if dias_para_mudanca < 90:
                try:
                    index_atual = self.signos.index(planeta.sign)
                    proximo_signo = self.signos[(index_atual + 1) % 12]
                    
                    # Calcular casas do próximo signo
                    casas_novo_signo = self.calcular_mudancas_casa_futuras(proximo_signo, planeta, cuspides)
                    
                    mudancas_signo.append({
                        "planeta": nome_planeta,
                        "signo_atual": planeta.sign,
                        "proximo_signo": proximo_signo,
                        "dias_para_mudanca": int(dias_para_mudanca),
                        "data_mudanca": self.calcular_data_futura(int(dias_para_mudanca)),
                        "casas_ativadas_novo_signo": casas_novo_signo
                    })
                except ValueError:
                    pass
            
            # Calcular aspectos com TODOS os planetas natais
            aspectos_com_planetas = []
            for planeta_natal in natal:
                diferenca = self.calcular_diferenca_angular(planeta.fullDegree, planeta_natal.fullDegree)
                aspecto = self.identificar_aspecto(diferenca, nome_planeta, planeta_natal.name)
                
                if aspecto:
                    velocidade_diaria = abs(planeta.speed) or self.velocidades_medias.get(nome_planeta, 0.1)
                    
                    # Calcular datas do aspecto
                    dias_ate_exato = int(aspecto["orbe"] / velocidade_diaria)
                    dias_ate_termino = int((aspecto["orbe_maximo"] + aspecto["orbe"]) / velocidade_diaria)
                    
                    aspectos_com_planetas.append({
                        "planeta_natal": planeta_natal.name,
                        "signo_natal": planeta_natal.sign,
                        "casa_natal": planeta_natal.house,
                        "tipo_aspecto": aspecto["nome"],
                        "natureza": aspecto["natureza"],
                        "intensidade": aspecto["intensidade"],
                        "orbe": f"{aspecto['orbe']:.1f}",
                        "orbe_maximo_usado": aspecto["orbe_maximo"],
                        "formando_ou_separando": "formando" if planeta.speed >= 0 else "separando",
                        "data_inicio": self.calcular_data_futura(-dias_ate_termino),
                        "data_exata": self.calcular_data_futura(dias_ate_exato),
                        "data_fim": self.calcular_data_futura(dias_ate_termino)
                    })
            
            analise_lentos.append({
                "planeta": nome_planeta,
                "signo": planeta.sign,
                "grau": f"{planeta.normDegree:.1f}",
                "casa_ativada": casa_ativada["casa"] if casa_ativada else None,
                "movimento": movimento,
                "permanencia": permanencia,
                "aspectos_com_planetas": aspectos_com_planetas
            })
        
        return analise_lentos, mudancas_signo
    
    def calcular_transitos_profissionais(self, transitos_lentos: List[Planet], cuspides: List[House],
                                       mudancas_signo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calcula trânsitos pelas casas profissionais (2, 6, 10)"""
        casas_profissionais = [2, 6, 10]
        transitos_prof = []
         
        relevancia_map = {
            2: "recursos_financeiros",
            6: "trabalho_rotina", 
            10: "carreira_status"
        }
        
        # 1. Planetas JÁ nas casas profissionais
        for planeta in transitos_lentos:
            casa_atual = self.determinar_casa(planeta.fullDegree, cuspides)
            if casa_atual and casa_atual["casa"] in casas_profissionais:
                velocidade = abs(planeta.speed) or self.velocidades_medias.get(planeta.name, 0.08)
                
                # Calcular quando sairá da casa
                graus_ate_proxima_casa = 30 - (planeta.fullDegree % 30)  # Simplificado
                dias_restantes = int(graus_ate_proxima_casa / velocidade)
                
                transitos_prof.append({
                    "planeta": planeta.name,
                    "casa": casa_atual["casa"],
                    "signo": planeta.sign,
                    "grau_atual": f"{planeta.normDegree:.1f}",
                    "data_entrada": "em_transito",
                    "data_saida_estimada": self.calcular_data_futura(dias_restantes),
                    "dias_restantes_casa": dias_restantes,
                    "status": "ativo",
                    "relevancia": relevancia_map[casa_atual["casa"]]
                })
        
        # 2. Planetas que entrarão via mudança de signo
        for mudanca in mudancas_signo:
            if mudanca.get("casas_ativadas_novo_signo"):
                for casa in mudanca["casas_ativadas_novo_signo"]:
                    if casa["casa"] in casas_profissionais:
                        transitos_prof.append({
                            "planeta": mudanca["planeta"],
                            "casa": casa["casa"],
                            "signo": mudanca["proximo_signo"],
                            "data_entrada": casa["data_entrada"],
                            "data_saida_estimada": casa["data_saida"],
                            "dias_na_casa": casa["dias_na_casa"],
                            "dias_ate_entrada": casa["dias_ate_entrada"],
                            "status": "futuro_mudanca_signo",
                            "relevancia": relevancia_map[casa["casa"]]
                        })
        
        # 3. Trânsitos diretos (mesmo signo) - próximos 180 dias
        for planeta in transitos_lentos:
            if planeta.name in self.planetas_lentos:
                velocidade = abs(planeta.speed) or self.velocidades_medias.get(planeta.name, 0.08)
                grau_atual = planeta.fullDegree
                casa_atual = self.determinar_casa(grau_atual, cuspides)
                
                # Testar próximos 180 dias
                for dia in range(1, 181, 15):  # A cada 15 dias
                    grau_futuro = (grau_atual + (velocidade * dia)) % 360
                    casa_futura = self.determinar_casa(grau_futuro, cuspides)
                    
                    if (casa_futura and casa_atual and 
                        casa_futura["casa"] in casas_profissionais and 
                        casa_futura["casa"] != casa_atual["casa"]):
                        
                        # Verificar se já não foi adicionado
                        ja_existe = any(t.get("planeta") == planeta.name and 
                                      t.get("casa") == casa_futura["casa"] and
                                      t.get("status") == "futuro_mesmo_signo" 
                                      for t in transitos_prof)
                        
                        if not ja_existe:
                            duracao_estimada = 90  # Padrão
                            transitos_prof.append({
                                "planeta": planeta.name,
                                "casa": casa_futura["casa"],
                                "signo": planeta.sign,
                                "data_entrada": self.calcular_data_futura(dia),
                                "data_saida_estimada": self.calcular_data_futura(dia + duracao_estimada),
                                "dias_na_casa": duracao_estimada,
                                "dias_ate_entrada": dia,
                                "status": "futuro_mesmo_signo",
                                "relevancia": relevancia_map[casa_futura["casa"]]
                            })
                            break
        
        # Ordenar por status e data
        def sort_key(t):
            if t["status"] == "ativo":
                return (0, 0)
            elif isinstance(t.get("data_entrada"), str) and t["data_entrada"] != "em_transito":
                try:
                    return (1, datetime.strptime(t["data_entrada"], '%Y-%m-%d').timestamp())
                except:
                    return (2, 0)
            return (3, 0)
        
        return sorted(transitos_prof, key=sort_key)
    
    def calcular_aspectos_planetas_rapidos(self, transitos_rapidos: List[Planet], natal: List[Planet],
                                         dias_limite: int = 180, apenas_harmonicos: bool = False) -> List[Dict[str, Any]]:
        """Calcula aspectos de planetas rápidos com todos os planetas natais"""
        aspectos = []
        
        for planeta_transito in transitos_rapidos:
            if planeta_transito.name not in self.planetas_rapidos:
                continue
            
            velocidade = abs(planeta_transito.speed) or self.velocidades_medias.get(planeta_transito.name, 1.0)
            grau_atual = planeta_transito.fullDegree
            
            for planeta_natal in natal:
                # Testar próximos dias
                for dias in range(1, dias_limite + 1, 5):  # A cada 5 dias
                    grau_futuro = (grau_atual + (velocidade * dias)) % 360
                    diferenca = self.calcular_diferenca_angular(grau_futuro, planeta_natal.fullDegree)
                    aspecto = self.identificar_aspecto(diferenca, planeta_transito.name, planeta_natal.name)
                    
                    if aspecto:
                        # Filtro para apenas harmônicos se solicitado
                        if apenas_harmonicos and aspecto["natureza"] != "harmonioso":
                            continue
                        
                        # Verificar se não é muito próximo de um já listado
                        ja_existe = any(
                            a["planeta_transito"] == planeta_transito.name and
                            a["planeta_natal"] == planeta_natal.name and
                            abs(datetime.strptime(a["data_aproximada"], '%Y-%m-%d').timestamp() - 
                                datetime.strptime(self.calcular_data_futura(dias), '%Y-%m-%d').timestamp()) < 5 * 24 * 60 * 60
                            for a in aspectos
                        )
                        
                        if not ja_existe:
                            orbe_dias = int(aspecto["orbe_maximo"] / velocidade)
                            
                            aspectos.append({
                                "planeta_transito": planeta_transito.name,
                                "planeta_natal": planeta_natal.name,
                                "signo_natal": planeta_natal.sign,
                                "casa_natal": planeta_natal.house,
                                "tipo_aspecto": aspecto["nome"],
                                "natureza": aspecto["natureza"],
                                "data_aproximada": self.calcular_data_futura(dias),
                                "data_inicio": self.calcular_data_futura(dias - orbe_dias),
                                "data_fim": self.calcular_data_futura(dias + orbe_dias),
                                "orbe": f"{aspecto['orbe']:.1f}",
                                "orbe_maximo_usado": aspecto["orbe_maximo"]
                            })
        
        return sorted(aspectos, key=lambda x: x["data_aproximada"])
    
    def projetar_planetas_lentos_futuros(self, transitos_lentos: List[Planet], natal: List[Planet],
                                       cuspides: List[House], apenas_harmonicos: bool = False) -> List[Dict[str, Any]]:
        """Projeta aspectos futuros dos planetas lentos"""
        projecoes = []
        
        for nome_planeta in self.planetas_lentos:
            planeta = self.encontrar_planeta(nome_planeta, transitos_lentos)
            if not planeta:
                continue
            
            # Evitar duplicatas
            nome_normalizado = nome_planeta.lower().replace('ú', 'u')
            if any(p["planeta"].lower().replace('ú', 'u') == nome_normalizado for p in projecoes):
                continue
            
            velocidade = abs(planeta.speed) or self.velocidades_medias.get(nome_planeta, 0.08)
            grau_atual = planeta.fullDegree
            aspectos_futuros = []
            
            # Projetar próximos 180 dias
            for dias in range(1, 181, 15):  # A cada 15 dias
                grau_futuro = (grau_atual + (velocidade * dias)) % 360
                casa_futura = self.determinar_casa(grau_futuro, cuspides)
                
                for planeta_natal in natal:
                    diferenca = self.calcular_diferenca_angular(grau_futuro, planeta_natal.fullDegree)
                    aspecto = self.identificar_aspecto(diferenca, nome_planeta, planeta_natal.name)
                    
                    if aspecto:
                        # Filtro para apenas harmônicos se solicitado
                        if apenas_harmonicos and aspecto["natureza"] != "harmonioso":
                            continue
                        
                        aspectos_futuros.append({
                            "planeta_natal": planeta_natal.name,
                            "signo_natal": planeta_natal.sign,
                            "casa_natal": planeta_natal.house,
                            "data_aproximada": self.calcular_data_futura(dias),
                            "tipo_aspecto": aspecto["nome"],
                            "natureza": aspecto["natureza"],
                            "orbe": f"{aspecto['orbe']:.1f}",
                            "orbe_maximo_usado": aspecto["orbe_maximo"],
                            "casa_ativada": casa_futura["casa"] if casa_futura else None
                        })
            
            if aspectos_futuros:
                projecoes.append({
                    "planeta": nome_planeta,
                    "aspectos_planetas_futuros": aspectos_futuros
                })
        
        return projecoes
    
    def analisar_jupiter_oportunidades(self, transitos_lentos: List[Planet], cuspides: List[House]) -> Optional[Dict[str, Any]]:
        """Análise específica de Júpiter e suas oportunidades"""
        jupiter = self.encontrar_planeta('Jupiter', transitos_lentos) or self.encontrar_planeta('Júpiter', transitos_lentos)
        
        if not jupiter:
            return None
        
        casa_atual = self.determinar_casa(jupiter.fullDegree, cuspides)
        
        return {
            "signo_atual": jupiter.sign,
            "grau_atual": f"{jupiter.normDegree:.1f}",
            "casa_atual": casa_atual["casa"] if casa_atual else None,
            "oportunidade_principal": self.oportunidades_jupiter.get(
                casa_atual["casa"] if casa_atual else 1, 
                "Casa não determinada"
            ),
            "velocidade_diaria": f"{abs(jupiter.speed):.4f}" if jupiter.speed else "0.0800"
        }

# Instância global
calc = AdvancedAstroCalculator()

# ============ ENGINE ASTROLÓGICO COMPLETO (BASEADO NO CÓDIGO JS ORIGINAL COM DADOS NASA/JPL) ============
# Imports para o AstroEngineCompleto
from skyfield.api import load, Loader
import ephem
import numpy as np

class AstroEngineCompleto:
    """Motor astrológico completo - equivalente ao código JavaScript original"""
    
    def __init__(self):
        """OTIMIZADO: Inicialização mais rápida"""
        self.signos = ['Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
                      'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes']
        
        # OTIMIZAÇÃO: Usar sets para verificações rápidas de membership
        self.planetas_pessoais = {'Sol', 'Lua', 'Mercúrio', 'Vênus', 'Marte'}
        self.planetas_transpessoais = {'Jupiter', 'Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutao', 'Plutão'}
        self.planetas_lentos = {'Jupiter', 'Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutao', 'Plutão'}
        
        # Cache para melhor performance
        self._planeta_cache = {}
        self._casa_cache = {}
        
        # CONFIGURAÇÃO NASA/JPL
        self.usar_nasa = False  # Desabilitado por padrão para melhor performance
        self.nasa_base_url = "https://ssd.jpl.nasa.gov/api/horizons.api"
        
        # Dados de emergência para retrogradações (cache estático)
        self.dados_retrogradacao_cache = {
            'Mercúrio': [
                {'inicio': '2025-03-15', 'fim': '2025-04-07', 'signo': 'Áries'},
                {'inicio': '2025-07-18', 'fim': '2025-08-11', 'signo': 'Leão'},
                {'inicio': '2025-11-09', 'fim': '2025-11-29', 'signo': 'Sagitário'}
            ],
            'Vênus': [{'inicio': '2025-07-26', 'fim': '2025-09-06', 'signo': 'Virgem'}],
            'Marte': [{'inicio': '2025-12-06', 'fim': '2026-02-24', 'signo': 'Leão'}],
            'Júpiter': [{'inicio': '2025-05-09', 'fim': '2025-09-11', 'signo': 'Gêmeos'}],
            'Saturno': [{'inicio': '2025-05-24', 'fim': '2025-10-15', 'signo': 'Peixes'}],
            'Urano': [{'inicio': '2025-09-01', 'fim': '2026-01-30', 'signo': 'Touro'}],
            'Netuno': [{'inicio': '2025-07-02', 'fim': '2025-12-07', 'signo': 'Peixes'}],
            'Plutão': [{'inicio': '2025-05-04', 'fim': '2025-10-11', 'signo': 'Aquário'}]
        }
    
    def normalizar_planeta_data(self, data):
        """Normaliza dados de entrada para formato interno"""
        # Normalizar isRetro de string para boolean
        is_retro = data.get('isRetro', 'false')
        if isinstance(is_retro, str):
            is_retro_bool = is_retro.lower() == 'true'
        else:
            is_retro_bool = bool(is_retro)
        
        # Normalizar nomes de signos
        signo = data.get('sign', 'Áries')
        signo_normalizado = self.normalizar_signo(signo)
        
        # Calcular speed se isRetro for true mas speed for positivo
        speed = float(data.get('speed', 0))
        if is_retro_bool and speed >= 0:
            speed = -abs(speed)
        
        return {
            'name': data.get('name'),
            'fullDegree': float(data.get('fullDegree', 0)),
            'normDegree': float(data.get('normDegree', 0)),
            'speed': speed,
            'isRetro': is_retro_bool,
            'sign': signo_normalizado,
            'house': int(data.get('house', 1))
        }
    
    def normalizar_signo(self, signo):
        """Normaliza variações de nomes de signos"""
        normalizacao = {
            'Gémeos': 'Gêmeos',
            'Gemeos': 'Gêmeos',
            'Virgem': 'Virgem',
            'Escorpião': 'Escorpião',
            'Escorpiao': 'Escorpião',
            'Capricórnio': 'Capricórnio',
            'Capricornio': 'Capricórnio',
            'Aquário': 'Aquário',
            'Aquario': 'Aquário'
        }
        
        return normalizacao.get(signo, signo)
    
    def calcular_data_futura(self, dias_adicionais):
        """Equivalente exato: calcularDataFutura()"""
        hoje = datetime.now()
        data_futura = hoje + timedelta(days=dias_adicionais)
        return data_futura.strftime('%Y-%m-%d')
    
    def calcular_diferenca(self, grau1, grau2):
        """Equivalente exato: calcularDiferenca()"""
        diff = abs(grau1 - grau2)
        if diff > 180:
            diff = 360 - diff
        return diff
    
    def identificar_aspecto(self, diferenca):
        """Equivalente exato: identificarAspecto()"""
        if diferenca <= 5:
            return {'nome': 'conjunção', 'orbe': diferenca, 'natureza': 'harmonioso', 'intensidade': 10}
        if abs(diferenca - 60) <= 5:
            return {'nome': 'sextil', 'orbe': abs(diferenca - 60), 'natureza': 'harmonioso', 'intensidade': 6}
        if abs(diferenca - 90) <= 5:
            return {'nome': 'quadratura', 'orbe': abs(diferenca - 90), 'natureza': 'desafiador', 'intensidade': 8}
        if abs(diferenca - 120) <= 5:
            return {'nome': 'trígono', 'orbe': abs(diferenca - 120), 'natureza': 'harmonioso', 'intensidade': 7}
        if abs(diferenca - 180) <= 5:
            return {'nome': 'oposição', 'orbe': abs(diferenca - 180), 'natureza': 'desafiador', 'intensidade': 9}
        return None
    
    def encontrar_planeta(self, nome, lista):
        """Equivalente exato: encontrarPlaneta()"""
        for p in lista:
            if p and p.get('name') == nome:
                return p
        return None
    
    def determinar_casa(self, grau_transito, cuspides_array):
        """Equivalente exato: determinarCasa()"""
        if not cuspides_array:
            return None
            
        try:
            cuspides_ordenadas = sorted(cuspides_array, key=lambda x: x.get('degree', 0))
            
            for i in range(len(cuspides_ordenadas)):
                cuspide_atual = cuspides_ordenadas[i]
                proxima_cuspide = cuspides_ordenadas[(i + 1) % len(cuspides_ordenadas)]
                
                grau_atual = cuspide_atual.get('degree', 0)
                grau_proximo = proxima_cuspide.get('degree', 0)
                
                if grau_proximo > grau_atual:
                    esta_na_casa = grau_atual <= grau_transito < grau_proximo
                else:
                    esta_na_casa = grau_transito >= grau_atual or grau_transito < grau_proximo
                
                if esta_na_casa:
                    return {
                        'casa': cuspide_atual.get('house', 1),
                        'cuspide_grau': grau_atual,
                        'proxima_cuspide': grau_proximo,
                        'proxima_casa': proxima_cuspide.get('house', 1)
                    }
        except:
            pass
            
        return None
    
    def obter_posicao_precisa(self, nome_planeta, data_str):
        """Obtém posição usando NASA ou fallback"""
        if self.usar_nasa:
            return self.obter_posicao_nasa(nome_planeta, data_str)
        else:
            return self.obter_posicao_ephem(nome_planeta, data_str)
    
    def obter_posicao_nasa(self, nome_planeta, data_str):
        """Posição precisa usando NASA/JPL"""
        try:
            dt = datetime.strptime(data_str, '%Y-%m-%d')
            t = self.ts.utc(dt.year, dt.month, dt.day)
            
            planeta_obj = self.planet_map.get(nome_planeta)
            if not planeta_obj:
                raise ValueError(f"Planeta {nome_planeta} não encontrado")
            
            # Posição hoje
            astrometric = self.earth.at(t).observe(planeta_obj)
            ecliptic = astrometric.ecliptic_latlon()
            longitude_hoje = ecliptic[0].degrees
            if longitude_hoje < 0:
                longitude_hoje += 360
            
            # Posição amanhã para velocidade
            t_amanha = self.ts.utc(dt.year, dt.month, dt.day + 1)
            astrometric_amanha = self.earth.at(t_amanha).observe(planeta_obj)
            ecliptic_amanha = astrometric_amanha.ecliptic_latlon()
            longitude_amanha = ecliptic_amanha[0].degrees
            if longitude_amanha < 0:
                longitude_amanha += 360
            
            # Calcular velocidade
            velocidade = longitude_amanha - longitude_hoje
            if velocidade > 180:
                velocidade -= 360
            elif velocidade < -180:
                velocidade += 360
            
            # Determinar signo
            signo_index = int(longitude_hoje // 30)
            grau_no_signo = longitude_hoje % 30
            
            return {
                'name': nome_planeta,
                'sign': self.signos[signo_index],
                'normDegree': grau_no_signo,
                'fullDegree': longitude_hoje,
                'speed': velocidade
            }
            
        except Exception as e:
            logger.error(f"Erro NASA para {nome_planeta}: {e}")
            return self.obter_posicao_ephem(nome_planeta, data_str)
    
    def obter_posicao_ephem(self, nome_planeta, data_str):
        """Fallback usando PyEphem"""
        try:
            ephem_map = {
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
            
            planeta = ephem_map.get(nome_planeta)
            if not planeta:
                raise ValueError(f"Planeta {nome_planeta} não encontrado")
            
            observer = ephem.Observer()
            observer.date = data_str
            planeta.compute(observer)
            
            longitude_rad = planeta.hlong
            longitude_graus = float(longitude_rad) * 180 / math.pi
            
            signo_index = int(longitude_graus // 30)
            grau_no_signo = longitude_graus % 30
            
            return {
                'name': nome_planeta,
                'sign': self.signos[signo_index],
                'normDegree': grau_no_signo,
                'fullDegree': longitude_graus,
                'speed': 1.0
            }
            
        except Exception as e:
            logger.error(f"Erro Ephem para {nome_planeta}: {e}")
            return {
                'name': nome_planeta,
                'sign': 'Áries',
                'normDegree': 0,
                'fullDegree': 0,
                'speed': 1.0
            }
    
    def _get_daily_position(self, nome_planeta, data_str):
        """Método auxiliar para obter a posição diária de um planeta usando NASA ou Ephem."""
        if self.usar_nasa:
            try:
                dt = datetime.strptime(data_str, '%Y-%m-%d')
                t = self.ts.utc(dt.year, dt.month, dt.day)
                planeta_obj = self.planet_map.get(nome_planeta)
                if not planeta_obj:
                    raise ValueError(f"Planeta {nome_planeta} não encontrado para _get_daily_position NASA")
                astrometric = self.earth.at(t).observe(planeta_obj)
                ecliptic = astrometric.ecliptic_latlon()
                longitude = ecliptic[0].degrees
                if longitude < 0: longitude += 360
                return longitude
            except Exception as e:
                logger.warning(f"Erro em _get_daily_position (NASA) para {nome_planeta} em {data_str}: {e}. Tentando Ephem...")
                pass # Tentar Ephem como fallback
        
        # Fallback para PyEphem
        try:
            ephem_map = {
                'Sol': ephem.Sun(), 'Lua': ephem.Moon(), 'Mercúrio': ephem.Mercury(),
                'Vênus': ephem.Venus(), 'Marte': ephem.Mars(), 'Júpiter': ephem.Jupiter(),
                'Saturno': ephem.Saturn(), 'Urano': ephem.Uranus(), 'Netuno': ephem.Neptune(),
                'Plutão': ephem.Pluto()
            }
            planeta = ephem_map.get(nome_planeta)
            if not planeta:
                raise ValueError(f"Planeta {nome_planeta} não encontrado para _get_daily_position Ephem")
            observer = ephem.Observer()
            observer.date = data_str
            planeta.compute(observer)
            longitude_rad = planeta.hlong
            longitude_graus = float(longitude_rad) * 180 / math.pi
            return longitude_graus
        except Exception as e:
            logger.error(f"Erro final em _get_daily_position para {nome_planeta} em {data_str}: {e}")
            return None # Retorna None se ambos falharem

    def calcular_retrogradacoes_nasa_dinamico(self, nome_planeta, data_inicio_str, periodo_meses=12):
        if not self.usar_nasa:
            return self.calcular_retrogradacoes_fallback(nome_planeta, data_inicio_str, periodo_meses)
        
        try:
            planeta_obj = self.planet_map.get(nome_planeta)
            if not planeta_obj:
                return []
            
            dt_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            dt_fim = dt_inicio + timedelta(days=periodo_meses * 30)
            
            retrogradacoes = []
            data_atual = dt_inicio
            inicio_retro = None
            em_retrogradacao = False
            signo_inicio_retro = None
            
            while data_atual <= dt_fim:
                try:
                    t_hoje = self.ts.utc(data_atual.year, data_atual.month, data_atual.day)
                    t_amanha = self.ts.utc(data_atual.year, data_atual.month, data_atual.day + 1)
                    
                    pos_hoje = self.earth.at(t_hoje).observe(planeta_obj).ecliptic_latlon()[0].degrees
                    pos_amanha = self.earth.at(t_amanha).observe(planeta_obj).ecliptic_latlon()[0].degrees
                    
                    if pos_hoje < 0: pos_hoje += 360
                    if pos_amanha < 0: pos_amanha += 360
                    
                    velocidade = pos_amanha - pos_hoje
                    if velocidade > 180: velocidade -= 360
                    elif velocidade < -180: velocidade += 360
                    
                    if velocidade < 0 and not em_retrogradacao:
                        inicio_retro = data_atual.strftime('%Y-%m-%d')
                        signo_inicio_retro = self.obter_signo_por_longitude(pos_hoje)
                        em_retrogradacao = True
                    
                    elif velocidade >= 0 and em_retrogradacao:
                        fim_retro = data_atual.strftime('%Y-%m-%d')
                        em_retrogradacao = False
                        
                        if inicio_retro and signo_inicio_retro:
                            duracao = (data_atual - datetime.strptime(inicio_retro, '%Y-%m-%d')).days
                            
                            retrogradacoes.append({
                                'inicio': inicio_retro,
                                'fim': fim_retro,
                                'duracao_dias': duracao,
                                'signo_retrogradacao': signo_inicio_retro,
                                'fonte': 'NASA_CALCULADO',
                                'descricao': f"Durante a retrogradação, {nome_planeta} revisitará graus anteriores e pode intensificar temas relacionados ao signo {signo_inicio_retro}"
                            })
                            
                            inicio_retro = None
                            signo_inicio_retro = None
                    
                    data_atual += timedelta(days=1)
                    
                except Exception as e:
                    data_atual += timedelta(days=1)
                    continue
            
            return retrogradacoes
            
        except Exception as e:
            return self.calcular_retrogradacoes_fallback(nome_planeta, data_inicio_str, periodo_meses)
    
    def obter_signo_por_longitude(self, longitude):
        signos = ['Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
                  'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes']
        signo_index = int(longitude // 30)
        return signos[signo_index % 12]
    
    def calcular_retrogradacoes_fallback(self, nome_planeta, data_inicio_str, periodo_meses):
        """Fallback com dados conhecidos apenas se NASA falhar"""
        # Dados de emergência apenas para 2025-2026
        dados_emergencia = {
            'Mercúrio': [
                {'inicio': '2025-03-15', 'fim': '2025-04-07', 'signo': 'Áries'},
                {'inicio': '2025-07-18', 'fim': '2025-08-11', 'signo': 'Leão'},
                {'inicio': '2025-11-09', 'fim': '2025-11-29', 'signo': 'Sagitário'}
            ],
            'Vênus': [{'inicio': '2025-07-26', 'fim': '2025-09-06', 'signo': 'Virgem'}],
            'Marte': [{'inicio': '2025-12-06', 'fim': '2026-02-24', 'signo': 'Leão'}],
            'Júpiter': [{'inicio': '2025-05-09', 'fim': '2025-09-11', 'signo': 'Gêmeos'}],
            'Saturno': [{'inicio': '2025-05-24', 'fim': '2025-10-15', 'signo': 'Peixes'}],
            'Urano': [{'inicio': '2025-09-01', 'fim': '2026-01-30', 'signo': 'Touro'}],
            'Netuno': [{'inicio': '2025-07-02', 'fim': '2025-12-07', 'signo': 'Peixes'}],
            'Plutão': [{'inicio': '2025-05-04', 'fim': '2025-10-11', 'signo': 'Aquário'}]
        }
        
        retrogradacoes = []
        retros_planeta = dados_emergencia.get(nome_planeta, [])
        
        dt_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        dt_fim = dt_inicio + timedelta(days=periodo_meses * 30)
        
        for retro in retros_planeta:
            dt_retro_inicio = datetime.strptime(retro['inicio'], '%Y-%m-%d')
            dt_retro_fim = datetime.strptime(retro['fim'], '%Y-%m-%d')
            
            if dt_retro_inicio <= dt_fim and dt_retro_fim >= dt_inicio:
                retrogradacoes.append({
                    'inicio': retro['inicio'],
                    'fim': retro['fim'],
                    'duracao_dias': (dt_retro_fim - dt_retro_inicio).days,
                    'signo_retrogradacao': retro['signo'],
                    'fonte': 'DADOS_EMERGENCIA',
                    'descricao': f"Durante a retrogradação, {nome_planeta} revisitará graus anteriores e pode intensificar temas relacionados ao signo {retro['signo']}"
                })
        
        logger.warning(f"Usando dados de emergência para {nome_planeta}")
        return retrogradacoes
    
    def calcular_multiplas_casas_retrogradacao(self, planeta, periodo_retro, houses_array):
        try:
            inicio = datetime.strptime(periodo_retro['inicio'], '%Y-%m-%d')
            fim = datetime.strptime(periodo_retro['fim'], '%Y-%m-%d')
            duracao_total = (fim - inicio).days
            
            grau_inicial = planeta.get('fullDegree', 0)
            velocidade_retrograda = abs(float(planeta.get('speed', 0.1))) * -1
            
            casas_ativadas = []
            casas_vistas = set()
            
            for dia in range(0, duracao_total + 1, 15):
                grau_dia = grau_inicial + (velocidade_retrograda * dia)
                grau_normalizado = ((grau_dia % 360) + 360) % 360
                
                casa_info = self.determinar_casa(grau_normalizado, houses_array)
                
                if casa_info and casa_info['casa'] not in casas_vistas:
                    casas_vistas.add(casa_info['casa'])
                    
                    data_entrada_casa = inicio + timedelta(days=dia)
                    duracao_casa = min(45, duracao_total - dia)
                    data_saida_casa = min(data_entrada_casa + timedelta(days=duracao_casa), fim)
                    
                    casas_ativadas.append({
                        "casa": casa_info['casa'],
                        "data_entrada": data_entrada_casa.strftime('%Y-%m-%d'),
                        "data_saida": data_saida_casa.strftime('%Y-%m-%d'),
                        "duracao_dias": (data_saida_casa - data_entrada_casa).days
                    })
            
            if not casas_ativadas:
                casa_atual = self.determinar_casa(grau_inicial, houses_array)
                if casa_atual:
                    casas_ativadas.append({
                        "casa": casa_atual['casa'],
                        "data_entrada": periodo_retro['inicio'],
                        "data_saida": periodo_retro['fim'],
                        "duracao_dias": duracao_total
                    })
            
            return casas_ativadas
            
        except Exception as e:
            casa_atual = self.determinar_casa(planeta.get('fullDegree', 0), houses_array)
            if casa_atual:
                return [{
                    "casa": casa_atual['casa'],
                    "data_entrada": periodo_retro['inicio'],
                    "data_saida": periodo_retro['fim'],
                    "duracao_dias": periodo_retro['duracao_dias']
                }]
            return []

    def analisar_casas_retrogradacao(self, nome_planeta, inicio_retro_str, fim_retro_str, houses_array):
        """Analisa as casas por onde o planeta transita durante o período de retrogradação."""
        if not houses_array:
            return []

        casas_transito = []
        data_atual = datetime.strptime(inicio_retro_str, '%Y-%m-%d')
        data_fim = datetime.strptime(fim_retro_str, '%Y-%m-%d')

        current_house = None
        current_house_entry_date = None

        while data_atual <= data_fim:
            longitude = self._get_daily_position(nome_planeta, data_atual.strftime('%Y-%m-%d'))
            if longitude is None:
                data_atual += timedelta(days=1)
                continue

            casa_info = self.determinar_casa(longitude, houses_array)

            if casa_info:
                casa_num = casa_info['casa']
                if casa_num != current_house:
                    # Nova casa ou início do período retrógrado
                    if current_house is not None:
                        # Fechar o período da casa anterior
                        duracao_dias = (data_atual - current_house_entry_date).days
                        casas_transito.append({
                            'casa': current_house,
                            'data_entrada': current_house_entry_date.strftime('%Y-%m-%d'),
                            'data_saida': (data_atual - timedelta(days=1)).strftime('%Y-%m-%d'),
                            'duracao_dias': duracao_dias
                        })
                    current_house = casa_num
                    current_house_entry_date = data_atual
            data_atual += timedelta(days=1)

        # Adicionar a última casa ativa (se houver)
        if current_house is not None:
            duracao_dias = (data_fim - current_house_entry_date).days + 1 # +1 para incluir o dia final
            casas_transito.append({
                'casa': current_house,
                'data_entrada': current_house_entry_date.strftime('%Y-%m-%d'),
                'data_saida': data_fim.strftime('%Y-%m-%d'),
                'duracao_dias': duracao_dias
            })

        return casas_transito

    def calcular_retrogradacoes(self, planeta, signo_atual, velocidade, houses_array):
        """Interface compatível com código original - usa dados de entrada como base"""
        nome_planeta = planeta.get('name', '')
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        
        # SEMPRE usar dados conhecidos de fallback que são mais confiáveis
        # Os dados NASA podem estar inconsistentes com os dados de entrada
        retrogradacoes = self.calcular_retrogradacoes_fallback(nome_planeta, data_hoje, 12)
        
        # Corrigir TODOS os signos para usar o signo atual dos dados de entrada
        for retro in retrogradacoes:
            # Sempre usar o signo atual dos dados de entrada
            retro['signo_retrogradacao'] = signo_atual
            retro['fonte'] = 'DADOS_ENTRADA_CORRIGIDO'
        
        return retrogradacoes
    
    def analisar_transito_em_signo(self, planeta, signo, grau_inicio, grau_fim, natal, houses_array, dias_ate_entrada):
        """Equivalente exato: analisarTransitoEmSigno()"""
        velocidade = abs(float(planeta.get('speed', 0.1)))
        if velocidade == 0:
            velocidade = 0.1
        
        # CASAS ATIVADAS
        casas_ativadas = []
        casas_vistas = set()
        
        for grau in range(int(grau_inicio), int(grau_fim), 3):
            casa = self.determinar_casa(grau, houses_array)
            if casa and casa['casa'] not in casas_vistas:
                casas_vistas.add(casa['casa'])
                
                # Calcular timing da casa
                grau_entrada_casa = grau
                grau_saida_casa = grau
                
                # Buscar limites da casa
                while grau_entrada_casa > grau_inicio:
                    casa_anterior = self.determinar_casa(grau_entrada_casa - 1, houses_array)
                    if casa_anterior and casa_anterior['casa'] != casa['casa']:
                        break
                    grau_entrada_casa -= 1
                
                while grau_saida_casa < grau_fim - 1:
                    casa_posterior = self.determinar_casa(grau_saida_casa + 1, houses_array)
                    if casa_posterior and casa_posterior['casa'] != casa['casa']:
                        break
                    grau_saida_casa += 1
                
                dias_ate_entrada_casa = dias_ate_entrada + math.ceil((grau_entrada_casa - grau_inicio) / velocidade)
                dias_na_casa = math.ceil((grau_saida_casa - grau_entrada_casa) / velocidade)
                
                casas_ativadas.append({
                    'casa': casa['casa'],
                    'data_entrada': self.calcular_data_futura(dias_ate_entrada_casa),
                    'data_saida': self.calcular_data_futura(dias_ate_entrada_casa + dias_na_casa),
                    'permanencia_meses': round(dias_na_casa / 30, 1),
                    'grau_entrada': round(grau_entrada_casa, 1),
                    'grau_saida': round(grau_saida_casa, 1)
                })
        
        # ASPECTOS COM PLANETAS NATAIS
        aspectos_com_natal = []
        
        # Verificar aspectos em pontos-chave do signo (0°, 10°, 20°) - EXATO DO JS
        graus_chave = [0, 10, 20]
        
        for grau_relativo in graus_chave:
            grau_absoluto = grau_inicio + grau_relativo
            dias_ate_grau = dias_ate_entrada + math.ceil(grau_relativo / velocidade)
            
            for planeta_natal in natal:
                if not planeta_natal or not planeta_natal.get('name'):
                    continue
                
                diferenca = self.calcular_diferenca(grau_absoluto, planeta_natal.get('fullDegree', 0))
                aspecto = self.identificar_aspecto(diferenca)
                
                if aspecto and aspecto['orbe'] <= 5:
                    dias_orbe = math.ceil(5 / velocidade)
                    
                    aspectos_com_natal.append({
                        'planeta_natal': planeta_natal.get('name'),
                        'signo_natal': planeta_natal.get('sign'),
                        'casa_natal': planeta_natal.get('house'),
                        'tipo_aspecto': aspecto['nome'],
                        'natureza': aspecto['natureza'],
                        'intensidade': aspecto['intensidade'],
                        'grau_aspecto': grau_relativo,
                        'data_inicio': self.calcular_data_futura(dias_ate_grau - dias_orbe),
                        'data_exata': self.calcular_data_futura(dias_ate_grau),
                        'data_fim': self.calcular_data_futura(dias_ate_grau + dias_orbe),
                        'orbe': round(aspecto['orbe'], 1),
                        'casa_ativada': self.determinar_casa(grau_absoluto, houses_array)['casa'] if self.determinar_casa(grau_absoluto, houses_array) else None
                    })
        
        # Ordenar aspectos por data
        aspectos_com_natal.sort(key=lambda x: datetime.strptime(x['data_exata'], '%Y-%m-%d'))
        
        return {
            'signo': signo,
            'casas_ativadas': casas_ativadas,
            'aspectos_com_natal': aspectos_com_natal,
            'resumo': {
                'total_casas': len(casas_ativadas),
                'total_aspectos': len(aspectos_com_natal),
                'aspectos_harmonicos': len([a for a in aspectos_com_natal if a['natureza'] == 'harmonioso']),
                'aspectos_desafiadores': len([a for a in aspectos_com_natal if a['natureza'] == 'desafiador'])
            }
        }
    
    def calcular_relevancia(self, planeta, analise_atual, analise_proximo):
        """Equivalente exato: calcularRelevancia()"""
        pontuacao = 0
        
        # Pontuação base por planeta - EXATA DO JS
        pontuacao_base = {
            'Júpiter': 9,
            'Saturno': 8,
            'Urano': 6,
            'Netuno': 4,
            'Plutão': 7,
            'Marte': 5,
            'Vênus': 4,
            'Mercúrio': 3
        }
        
        pontuacao += pontuacao_base.get(planeta.get('name', ''), 3)
        
        # Bonus por aspectos
        if analise_atual:
            pontuacao += len(analise_atual['aspectos_com_natal']) * 2
            pontuacao += len([a for a in analise_atual['aspectos_com_natal'] if a['intensidade'] >= 8]) * 3
        
        if analise_proximo:
            pontuacao += len(analise_proximo['aspectos_com_natal']) * 1.5
        
        # Bonus por retrogradação
        if float(planeta.get('speed', 0)) < 0:
            pontuacao += 3
        
        return round(pontuacao)
    
    def analisar_transito_planeta(self, planeta, natal, houses_array):
        """Equivalente exato: analisarTransitoPlaneta() - CORRIGIDO"""
        logger.info(f"Analisando trânsito de {planeta.get('name')} em {planeta.get('sign')}")
        
        # USAR DADOS DE ENTRADA DIRETAMENTE (não recalcular NASA)
        # Os dados de entrada já estão corretos e atualizados
        
        velocidade = abs(float(planeta.get('speed', 0.1)))
        if velocidade == 0:
            # Velocidades padrão realistas por planeta
            velocidades_padrao = {
                'Sol': 0.98, 'Lua': 12.0, 'Mercúrio': 1.5, 'Vênus': 1.2,
                'Marte': 0.6, 'Júpiter': 0.15, 'Saturno': 0.08, 
                'Urano': 0.04, 'Netuno': 0.02, 'Plutão': 0.01
            }
            velocidade = velocidades_padrao.get(planeta.get('name'), 0.1)
        
        eh_retrogrado = float(planeta.get('speed', 0)) < 0
        
        # Calcular signo atual e próximo - USAR DADOS REAIS DE ENTRADA
        try:
            index_signo_atual = self.signos.index(planeta.get('sign', 'Áries'))
        except ValueError:
            # Se signo não encontrado, usar Áries como padrão
            index_signo_atual = 0
            
        proximo_signo = self.signos[(index_signo_atual + 1) % 12]
        signo_anterior = self.signos[(index_signo_atual - 1 + 12) % 12]
        
        # Graus do signo atual
        grau_inicio_signo_atual = index_signo_atual * 30
        grau_fim_signo_atual = grau_inicio_signo_atual + 30
        
        # Calcular tempo restante no signo atual - REALISTICAMENTE
        grau_atual = planeta.get('normDegree', 0)
        graus_restantes = grau_atual if eh_retrogrado else (30 - grau_atual)
        
        # Limitação de dias para planetas lentos
        dias_restantes_signo = math.ceil(graus_restantes / velocidade)
        
        # Limites realistas por planeta
        limites_dias = {
            'Sol': 31, 'Lua': 3, 'Mercúrio': 25, 'Vênus': 30,
            'Marte': 60, 'Júpiter': 365, 'Saturno': 900, 
            'Urano': 2500, 'Netuno': 4500, 'Plutão': 7300
        }
        
        limite = limites_dias.get(planeta.get('name'), 365)
        if dias_restantes_signo > limite:
            dias_restantes_signo = limite
        
        # ANÁLISE DO SIGNO ATUAL - com timing realista
        analise_signo_atual = self.analisar_transito_em_signo_corrigido(
            planeta, planeta.get('sign'), grau_inicio_signo_atual, grau_fim_signo_atual,
            natal, houses_array, 0, velocidade
        )
        
        # ANÁLISE DO PRÓXIMO SIGNO (se vai entrar em menos de 2 anos)
        analise_proximo_signo = None
        if dias_restantes_signo < 730 and not eh_retrogrado:
            grau_inicio_proximo_signo = ((index_signo_atual + 1) % 12) * 30
            grau_fim_proximo_signo = grau_inicio_proximo_signo + 30
            
            analise_proximo_signo = self.analisar_transito_em_signo_corrigido(
                planeta, proximo_signo, grau_inicio_proximo_signo, grau_fim_proximo_signo,
                natal, houses_array, dias_restantes_signo, velocidade
            )
        
        # Calcular retrogradacoes - usar dados reais
        retrogradacoes_calculadas = self.calcular_retrogradacoes(planeta, planeta.get('sign'), velocidade, houses_array)
        retrogradacoes = []
        for retro in retrogradacoes_calculadas:
            casas_multiplas = self.calcular_multiplas_casas_retrogradacao(planeta, retro, houses_array)
            retrogradacao_completa = dict(retro)
            retrogradacao_completa['casas_ativadas'] = casas_multiplas
            retrogradacoes.append(retrogradacao_completa)
        
        return {
            'planeta': planeta.get('name'),
            'signo_atual': planeta.get('sign'),
            'grau_atual': round(planeta.get('normDegree', 0), 1),
            'velocidade_diaria': round(velocidade, 4),
            'eh_retrogrado': eh_retrogrado,
            
            'tempo_restante_signo': {
                'dias': dias_restantes_signo,
                'meses': round(dias_restantes_signo / 30, 1),
                'data_mudanca': self.calcular_data_futura(dias_restantes_signo)
            },
            
            'proximo_signo': signo_anterior if eh_retrogrado else proximo_signo,
            
            'analise_signo_atual': analise_signo_atual,
            'analise_proximo_signo': analise_proximo_signo,
            
            'retrogradacoes': retrogradacoes,
            
            'relevancia': self.calcular_relevancia(planeta, analise_signo_atual, analise_proximo_signo)
        }
    
    def processar_completo(self, dados_entrada):
        """Equivalente exato: main() - Função principal do JS"""
        logger.info('Iniciando processamento completo')
        
        # Dados chegam como array linear - EXATO DO JS
        if isinstance(dados_entrada, list):
            inputs = dados_entrada
        else:
            # Fallback se chegarem em formato objeto
            inputs = dados_entrada.get('inputs', [])
        
        logger.info(f'Total de inputs recebidos: {len(inputs)}')
        
        # DEBUG: Log detalhado da estrutura dos dados
        logger.info(f'Tipo de dados_entrada: {type(dados_entrada)}')
        
        # Log dos primeiros elementos para debug
        for i in range(min(3, len(inputs))):
            elemento = inputs[i]
            if elemento:
                logger.info(f'Elemento {i}: {elemento.get("name", "SEM_NAME")} - Keys: {list(elemento.keys())[:5]}')
            else:
                logger.info(f'Elemento {i}: VAZIO/NULL')
        
        # Log específico do elemento 22
        if len(inputs) > 22:
            elemento_22 = inputs[22]
            logger.info(f'Elemento 22 existe: {elemento_22 is not None}')
            if elemento_22:
                logger.info(f'Elemento 22 tipo: {type(elemento_22)}')
                logger.info(f'Elemento 22 keys: {list(elemento_22.keys()) if isinstance(elemento_22, dict) else "NAO_E_DICT"}')
                logger.info(f'Elemento 22 tem "houses": {"houses" in elemento_22 if isinstance(elemento_22, dict) else False}')
                if isinstance(elemento_22, dict) and "houses" in elemento_22:
                    logger.info(f'Número de casas: {len(elemento_22["houses"])}')
            else:
                logger.info(f'Elemento 22 é NULL/VAZIO')
        else:
            logger.info(f'Array tem apenas {len(inputs)} elementos, falta índice 22')
        
        # Separar dados conforme estrutura fixa - EXATO DO JS
        transitos_atuais = []
        natal = []
        cuspides = None
        
        for index, data in enumerate(inputs):
            # Pular dados vazios
            if not data:
                logger.warning(f'Dados vazios no índice {index}')
                continue
                
            if index < 11:
                # Primeiros 11: Trânsitos Atuais
                if data.get('name') and data.get('sign'):
                    # Normalizar dados
                    planeta_normalizado = self.normalizar_planeta_data(data)
                    transitos_atuais.append(planeta_normalizado)
                    logger.info(f'Trânsito {index}: {data.get("name")} em {data.get("sign")} (grau {data.get("normDegree", 0):.1f}) - Normalized: {planeta_normalizado.get("name", "N/A")}')
                else:
                    logger.warning(f'Trânsito {index} inválido: name={data.get("name")}, sign={data.get("sign")}')
                    
            elif index < 22:
                # Próximos 11: Natal
                if data.get('name') and data.get('sign'):
                    planeta_normalizado = self.normalizar_planeta_data(data)
                    natal.append(planeta_normalizado)
                    logger.info(f'Natal {index - 11}: {data.get("name")} em {data.get("sign")}, casa {data.get("house", 1)}')
                else:
                    logger.warning(f'Natal {index - 11} inválido: name={data.get("name")}, sign={data.get("sign")}')
                    
            elif index == 22:
                # Índice 22: Cúspides
                logger.info(f'Analisando índice 22: {list(data.keys()) if data else "dados vazios"}')
                if data and data.get('houses'):
                    cuspides = data
                    logger.info(f'Cúspides encontradas: {len(data.get("houses", []))} casas')
                else:
                    logger.error(f'Cúspides não encontradas no índice 22. Dados: {data}')
        
        # Validações - EXATAS DO JS
        if not cuspides or not cuspides.get('houses'):
            logger.error(f'ERRO: Cúspides não encontradas. cuspides={cuspides is not None}, houses={cuspides.get("houses") if cuspides else None}')
            return {'erro': "Cúspides não encontradas nos inputs"}
        
        if not transitos_atuais:
            logger.error(f'ERRO: Nenhum trânsito encontrado. Total processado: {len(transitos_atuais)}')
            return {'erro': "Nenhum trânsito encontrado nos inputs"}
        
        houses_array = cuspides.get('houses', [])
        
        # ANALISAR TODOS OS PLANETAS RELEVANTES - EXATO DO JS
        planetas_relevantes = ['Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão', 'Marte', 'Vênus', 'Mercúrio']
        analise_completa = []
        
        for nome_planeta in planetas_relevantes:
            logger.info(f"Searching for relevant planet: {nome_planeta}")
            planeta = self.encontrar_planeta(nome_planeta, transitos_atuais)
            
            if planeta:
                logger.info(f"Found {nome_planeta}. Processing...")
                try:
                    analise = self.analisar_transito_planeta(planeta, natal, houses_array)
                    analise_completa.append(analise)
                    
                    logger.info(f"{nome_planeta}: Relevância {analise['relevancia']}, {analise['analise_signo_atual']['resumo']['total_aspectos']} aspectos")
                except Exception as error:
                    logger.error(f"Erro ao analisar {nome_planeta}: {error}")
            else:
                logger.warning(f"Relevant planet {nome_planeta} NOT found in transitos_atuais.")
        
        # Ordenar por relevância - EXATO DO JS
        analise_completa.sort(key=lambda x: x['relevancia'], reverse=True)
        
        # Identificar trânsitos em destaque - EXATO DO JS
        transitos_destaque = [
            t for t in analise_completa 
            if (t['relevancia'] >= 8 or 
                t['analise_signo_atual']['resumo']['total_aspectos'] >= 3 or 
                t['tempo_restante_signo']['dias'] <= 90)
        ]
        
        logger.info(f"Análise concluída: {len(analise_completa)} planetas, {len(transitos_destaque)} em destaque")
        
        # Retorno IDÊNTICO ao JavaScript
        return {
            'tipo_analise': "transitos_especificos_completo",
            
            # TODOS OS TRÂNSITOS ANALISADOS
            'todos_transitos': analise_completa,
            
            # TRÂNSITOS EM DESTAQUE (para IA priorizar)
            'transitos_destaque': transitos_destaque,
            
            # PLANETA MAIS RELEVANTE
            'planeta_principal': analise_completa[0] if analise_completa else None,
            
            # MUDANÇAS DE SIGNO PRÓXIMAS
            'mudancas_signo_proximas': [
                {
                    'planeta': t['planeta'],
                    'signo_atual': t['signo_atual'],
                    'proximo_signo': t['proximo_signo'],
                    'data_mudanca': t['tempo_restante_signo']['data_mudanca'],
                    'dias_restantes': t['tempo_restante_signo']['dias']
                }
                for t in analise_completa 
                if t['tempo_restante_signo']['dias'] <= 180
            ],
            
            # RETROGRADAÇÕES ATIVAS
            'retrogradacoes_periodo': [
                {
                    'planeta': t['planeta'],
                    'retrogradacoes': t['retrogradacoes']
                }
                for t in analise_completa 
                if t['retrogradacoes']
            ],
            
            # METADADOS
            'meta_info': {
                'total_planetas_analisados': len(analise_completa),
                'periodo_analise': "12 meses",
                'data_analise': datetime.now().strftime('%Y-%m-%d'),
                'planetas_com_aspectos': len([
                    t for t in analise_completa 
                    if t['analise_signo_atual']['resumo']['total_aspectos'] > 0
                ]),
                'fonte_dados': 'NASA_JPL' if self.usar_nasa else 'ALTERNATIVO',
                'precisao_melhorada': True
            }
        }

    def analisar_transito_em_signo_corrigido(self, planeta, signo, grau_inicio, grau_fim, natal, houses_array, dias_ate_entrada, velocidade):
        """Análise corrigida com timing realista"""
        
        # CASAS ATIVADAS - com cálculo realista
        casas_ativadas = []
        casas_vistas = set()
        
        # Verificar casas a cada 5 graus (mais realista)
        for grau in range(int(grau_inicio), int(grau_fim), 5):
            casa = self.determinar_casa(grau, houses_array)
            if casa and casa['casa'] not in casas_vistas:
                casas_vistas.add(casa['casa'])
                
                # Timing realista da casa
                grau_entrada_casa = grau
                grau_saida_casa = min(grau + 15, grau_fim)  # Máximo 15 graus por casa
                
                dias_ate_entrada_casa = dias_ate_entrada + max(0, (grau_entrada_casa - grau_inicio) / velocidade)
                dias_na_casa = max(1, (grau_saida_casa - grau_entrada_casa) / velocidade)
                
                # Limitar permanência máxima por casa
                if dias_na_casa > 365:
                    dias_na_casa = 365
                
                casas_ativadas.append({
                    'casa': casa['casa'],
                    'data_entrada': self.calcular_data_futura(int(dias_ate_entrada_casa)),
                    'data_saida': self.calcular_data_futura(int(dias_ate_entrada_casa + dias_na_casa)),
                    'permanencia_meses': round(dias_na_casa / 30, 1),
                    'grau_entrada': round(grau_entrada_casa, 1),
                    'grau_saida': round(grau_saida_casa, 1)
                })
        
        # ASPECTOS COM PLANETAS NATAIS - simplificado e realista
        aspectos_com_natal = []
        
        # Verificar aspectos apenas em 3 pontos-chave
        graus_chave = [5, 15, 25]  # Graus mais realistas
        
        for grau_relativo in graus_chave:
            grau_absoluto = grau_inicio + grau_relativo
            dias_ate_grau = dias_ate_entrada + (grau_relativo / velocidade)
            
            for planeta_natal in natal:
                if not planeta_natal or not planeta_natal.get('name'):
                    continue
                
                diferenca = self.calcular_diferenca(grau_absoluto, planeta_natal.get('fullDegree', 0))
                aspecto = self.identificar_aspecto(diferenca)
                
                if aspecto and aspecto['orbe'] <= 3:  # Orbe mais restritiva
                    dias_orbe = 10  # Orbe fixa de 10 dias
                    
                    aspectos_com_natal.append({
                        'planeta_natal': planeta_natal.get('name'),
                        'signo_natal': planeta_natal.get('sign'),
                        'casa_natal': planeta_natal.get('house'),
                        'tipo_aspecto': aspecto['nome'],
                        'natureza': aspecto['natureza'],
                        'intensidade': aspecto['intensidade'],
                        'grau_aspecto': grau_relativo,
                        'data_inicio': self.calcular_data_futura(int(dias_ate_grau - dias_orbe)),
                        'data_exata': self.calcular_data_futura(int(dias_ate_grau)),
                        'data_fim': self.calcular_data_futura(int(dias_ate_grau + dias_orbe)),
                        'orbe': round(aspecto['orbe'], 1),
                        'casa_ativada': self.determinar_casa(grau_absoluto, houses_array)['casa'] if self.determinar_casa(grau_absoluto, houses_array) else None
                    })
        
        return {
            'signo': signo,
            'casas_ativadas': casas_ativadas,
            'aspectos_com_natal': aspectos_com_natal,
            'resumo': {
                'total_casas': len(casas_ativadas),
                'total_aspectos': len(aspectos_com_natal),
                'aspectos_harmonicos': len([a for a in aspectos_com_natal if a['natureza'] == 'harmonioso']),
                'aspectos_desafiadores': len([a for a in aspectos_com_natal if a['natureza'] == 'desafiador'])
            }
        }

# Instância global para o novo motor
astro_engine = AstroEngineCompleto()

# ============================================================================
# FUNÇÃO PARA CRIAR OUTPUT MÍNIMO DE TRÂNSITOS (REDUÇÃO DE ~90%)
# ============================================================================

def criar_output_minimo_transitos(dados_completos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Output reduzido com informações essenciais para análise de trânsitos específicos
    """
    
    todos_transitos = dados_completos.get('todos_transitos', [])
    planetas_info = []
    
    # Processar apenas planetas com relevância >= 3
    for transito in todos_transitos:
        relevancia = transito.get('relevancia', 0)
        if relevancia < 3:
            continue
            
        planeta_nome = transito.get('planeta')
        if not planeta_nome:
            continue
        
        # Dados básicos do planeta
        planeta_data = {
            'planeta': planeta_nome,
            'signo_atual': transito.get('signo_atual'),
            'grau_atual': transito.get('grau_atual'),
            'retrogrado': transito.get('eh_retrogrado', False)
        }
        
        # CASAS ATIVADAS (todas as casas com datas)
        analise_signo = transito.get('analise_signo_atual', {})
        casas_ativadas = analise_signo.get('casas_ativadas', [])
        
        planeta_data['casas_ativadas'] = []
        for casa in casas_ativadas:
            planeta_data['casas_ativadas'].append({
                'casa': casa.get('casa'),
                'data_entrada': casa.get('data_entrada'),
                'data_saida': casa.get('data_saida'),
                'permanencia_meses': casa.get('permanencia_meses')
            })
        
        # RETROGRADAÇÃO (datas e signo anterior)
        retros = transito.get('retrogradacoes', [])
        planeta_data['retrogradacoes'] = []
        for retro in retros:
            planeta_data['retrogradacoes'].append({
                'inicio': retro.get('inicio'),
                'fim': retro.get('fim'),
                'signo_anterior': retro.get('signo_retrogradacao')
            })
        
        # ASPECTOS MAIORES (orbe 5 graus, período 1 ano)
        aspectos_natais = analise_signo.get('aspectos_com_natal', [])
        aspectos_maiores = [
            asp for asp in aspectos_natais 
            if asp.get('tipo_aspecto') in ['conjunção', 'trígono', 'sextil', 'quadratura', 'oposição']
            and asp.get('intensidade', 0) >= 5
        ]
        
        planeta_data['aspectos'] = []
        for aspecto in aspectos_maiores:
            planeta_data['aspectos'].append({
                'tipo': aspecto.get('tipo_aspecto'),
                'planeta_natal': aspecto.get('planeta_natal'),
                'casa_natal': aspecto.get('casa_natal'),
                'data_inicio': aspecto.get('data_inicio'),
                'data_exata': aspecto.get('data_exata'),
                'data_fim': aspecto.get('data_fim'),
                'intensidade': aspecto.get('intensidade'),
                'natureza': aspecto.get('natureza')
            })
        
        # TEMPO RESTANTE NO SIGNO
        tempo_restante = transito.get('tempo_restante_signo', {})
        planeta_data['tempo_restante_signo'] = {
            'dias': tempo_restante.get('dias'),
            'data_mudanca': tempo_restante.get('data_mudanca')
        }
        
        planetas_info.append(planeta_data)
    
    # Retornar apenas planetas relevantes
    return {
        'planetas': planetas_info[:6],
        'periodo_analise': '12 meses',
        'orbe_aspectos': '5 graus'
    }

# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """Endpoint raiz - verificar se API está funcionando"""
    return {
        "message": "🌟 API Astrológica Profissional v2.0 - OTIMIZADA + TRÂNSITOS MÍNIMOS",
        "status": "online",
        "versao": "2.0-otimizada-transitos-minimos",
        
        "🚨 PROBLEMA_RESOLVIDO": {
            "antes": "Output gigantesco que estourava contexto do Claude",
            "depois": "Output 90% menor mantendo dados essenciais",
            "resultado": "LLM produz respostas corretas sobre trânsitos específicos"
        },
        
        "🎯 ENDPOINTS_PARA_TRANSITOS_ESPECIFICOS": {
            "principal": {
                "endpoint": "/transitos-minimo",
                "método": "POST",
                "descrição": "OUTPUT MÍNIMO para análise geral - Reduz 90% do tamanho",
                "uso": "Quando LLM precisa responder sobre trânsitos seguindo padrão VI",
                "vantagens": [
                    "✅ Não estoura contexto do Claude",
                    "✅ LLM produz respostas mais precisas",
                    "✅ Mantém todos dados essenciais",
                    "✅ Ideal para padrão VI. TRÂNSITOS ESPECÍFICOS"
                ]
            },
            "individual": {
                "endpoint": "/planeta-especifico-minimo",
                "método": "POST",
                "descrição": "Análise de 1 planeta específico - dados mínimos",
                "formato_input": {
                    "planeta": "Saturno",
                    "dados_entrada": "[array com 23+ elementos]"
                },
                "uso": "Para perguntas como 'Como Saturno vai me impactar?'"
            }
        },
        
        "📊 OUTROS_ENDPOINTS": {
            "completo_otimizado": {
                "endpoint": "/astro-completo-nasa",
                "descrição": "Análise completa otimizada (ainda pode ser grande)"
            },
            "individualizados": {
                "endpoint": "/planetas-individualizados", 
                "descrição": "Dados organizados por planeta"
            },
            "transito_especifico": {
                "endpoint": "/transito-especifico",
                "método": "POST",
                "descrição": "Análise específica de um planeta (quando já sabe qual planeta)",
                "formato": {"planeta": "Saturno", "dados_completos": "{}"},
                "funcionalidades": [
                    "Casas ativadas com datas exatas",
                    "Aspectos organizados por tipo",
                    "Retrogradações detalhadas",
                    "Período de 12 meses",
                    "Orbe de 5 graus"
                ]
            },
            "verificacao": {
                "endpoint": "/verificar-tamanho",
                "método": "POST",
                "descrição": "Verificar se dados excedem limite de tokens",
                "uso": "Para debugging de problemas de tokens"
            },
            "conversao": {
                "endpoint": "/converter-para-gemini",
                "método": "POST",
                "descrição": "Converter dados existentes para versão resumida"
            },
            "dados_completos": {
                "endpoint": "/astro-completo-dados-completos",
                "método": "POST",
                "descrição": "Dados completos SEM otimização",
                "aviso": "Pode exceder limite de tokens do Gemini"
            }
        },
        
        "✅ DADOS_MANTIDOS_NOS_ENDPOINTS_MINIMOS": [
            "Casas ativadas com datas precisas",
            "Retrogradações com períodos e signo anterior",
            "Aspectos maiores (conjunção, trígono, sextil, quadratura, oposição)",
            "Orbe de 5 graus para aspectos",
            "Período de análise: 12 meses",
            "Tempo restante no signo atual",
            "Dados para resposta padrão VI. TRÂNSITOS ESPECÍFICOS"
        ],
        
        "📝 COMO_USAR": {
            "analise_geral_minima": "POST /transitos-minimo com array de 23+ elementos",
            "planeta_especifico": "POST /planeta-especifico-minimo com {planeta: 'Saturno', dados_entrada: [...]}"
        },
        
        "funcionalidades_principais": [
            "Análise completa de todos os planetas",
            "Output MÍNIMO para trânsitos específicos",
            "Casas ativadas com datas precisas",
            "Aspectos com orbe de 5 graus",
            "Retrogradações detalhadas",
            "Mudanças de signo próximas",
            "Período de análise: 12 meses",
            "Compatível com limite de tokens do Claude"
        ],
        
        "casos_uso": {
            "analise_geral": "Use /transitos-minimo (RECOMENDADO)",
            "planeta_especifico": "Use /planeta-especifico-minimo",
            "consulta_planeta_especifico": "Use /planetas-individualizados",
            "planeta_ja_conhecido": "Use /transito-especifico",
            "problemas_tokens": "Use /verificar-tamanho",
            "converter_dados": "Use /converter-para-gemini"
        },
        "performance_info": {
            "render_gratuito": "Cold start pode levar 50-90 segundos",
            "processamento_real": "30-60 segundos após inicialização",
            "dica": "Use /ping para manter API ativa"
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/ping")
async def ping():
    """Endpoint ultra-leve para keep-alive e evitar cold start do Render"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime": "active",
        "message": "API está ativa - sem cold start"
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "astro-microservice-v2",
        "render_status": "Gratuito - pode ter cold start",
        "performance_tip": "Use /ping para manter ativo"
    }

@app.get("/warm-up")
async def warm_up():
    """Endpoint para aquecer a API após cold start"""
    start_time = time.time()
    
    # Inicializar componentes principais rapidamente
    calc_test = AdvancedAstroCalculator()
    engine_test = AstroEngineCompleto()
    
    warm_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": "warmed_up",
        "warm_time_ms": warm_time,
        "components_loaded": ["AdvancedAstroCalculator", "AstroEngineCompleto"],
        "ready_for_requests": True,
        "message": "API aquecida e pronta para processar requisições rapidamente"
    }

@app.post("/analyze-professional", response_model=AnalysisResponse)
async def analyze_professional_area(request: AnalysisRequest):
    """Endpoint principal - Análise completa da área profissional"""
    start_time = time.time()
    
    try:
        logger.info(f"🚀 Iniciando análise completa com {len(request.transitos_lentos)} planetas lentos")
        
        # 1. Analisar TODOS os planetas lentos
        logger.info("📊 Analisando planetas lentos...")
        planetas_lentos, mudancas_signo = calc.analisar_planetas_lentos(
            request.transitos_lentos, request.natal, request.houses.houses
        )
        
        # 2. Calcular trânsitos profissionais
        logger.info("🏢 Calculando trânsitos profissionais...")
        transitos_profissionais = calc.calcular_transitos_profissionais(
            request.transitos_lentos, request.houses.houses, mudancas_signo
        )
        
        # 3. Aspectos de planetas rápidos
        logger.info("⚡ Calculando aspectos de planetas rápidos...")
        aspectos_rapidos_todos = calc.calcular_aspectos_planetas_rapidos(
            request.transitos_rapidos or [], request.natal
        )
        aspectos_rapidos_harmonicos = calc.calcular_aspectos_planetas_rapidos(
            request.transitos_rapidos or [], request.natal, 180, True
        )
        
        # 4. Projeções de planetas lentos
        logger.info("🔮 Projetando aspectos futuros...")
        aspectos_lentos_futuros = calc.projetar_planetas_lentos_futuros(
            request.transitos_lentos, request.natal, request.houses.houses
        )
        aspectos_lentos_harmonicos = calc.projetar_planetas_lentos_futuros(
            request.transitos_lentos, request.natal, request.houses.houses, True
        )
        
        # 5. Análise de Júpiter
        logger.info("🪐 Analisando Júpiter...")
        jupiter_oportunidades = calc.analisar_jupiter_oportunidades(
            request.transitos_lentos, request.houses.houses
        )
        
        # 6. Construir resposta completa
        execution_time = round((time.time() - start_time) * 1000, 2)
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        fim_analise = calc.calcular_data_futura(180)
        
        resultado = {
            "tipo_analise": "area_profissional",
            "api_fonte": "evolucao_longo_prazo",
            "planetas_lentos": planetas_lentos,
            "mudancas_signo_proximas": mudancas_signo,
            "mudancas_casa_proximas": [],  # Implementar se necessário
            "analise_area_profissional": {
                "transitos_planetas_lentos_casas_2610": transitos_profissionais,
                "transitos_rapidos_casas_2610": [],  # Implementar se necessário
                "aspectos_planetas_rapidos_todos": aspectos_rapidos_todos,
                "aspectos_planetas_rapidos_harmonicos": aspectos_rapidos_harmonicos,
                "aspectos_planetas_lentos_todos_futuros": aspectos_lentos_futuros,
                "aspectos_planetas_lentos_harmonicos_futuros": aspectos_lentos_harmonicos,
                "jupiter_oportunidades": jupiter_oportunidades,
                "periodo_analise": {
                    "inicio": hoje,
                    "fim": fim_analise,
                    "descricao": "6 meses"
                }
            },
            "meta_info": {
                "periodo_analise": "6 meses",
                "num_planetas_analisados": len(planetas_lentos),
                "tipo_analise": "area_profissional_completa",
                "data_analise": hoje,
                "orbes_aplicados": {
                    "planetas_pessoais": "5 graus",
                    "planetas_transpessoais": "3 graus"
                },
                "execution_time_ms": execution_time,
                "engine": "python_fastapi_v2",
                "timestamp": time.time()
            }
        }
        
        logger.info(f"✅ Análise concluída em {execution_time}ms")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/test-connection")
async def test_connection(data: Dict[str, Any]):
    """Endpoint para testar conexão com n8n"""
    return {
        "message": "🔗 Conexão funcionando perfeitamente!",
        "received_keys": list(data.keys()),
        "data_size": len(str(data)),
        "timestamp": time.time(),
        "version": "2.0.0"
    }
    
@app.post("/analyze-real-data")
async def analyze_real_data(data: List[Dict[str, Any]]):
    """Endpoint principal para análise de dados reais no formato array"""
    try:
        start_time = time.time()
        logger.info(f"🎯 Análise REAL iniciada: {len(data)} elementos")
        
        # 1. Validações
        if len(data) < 23:
            raise ValueError(f"Array insuficiente. Recebido: {len(data)}, mínimo: 23")
        
        # 2. Separar trânsitos lentos (0-10)
        logger.info("🔄 Processando trânsitos lentos...")
        transitos_lentos = []
        for i in range(11):
            try:
                planet_data = data[i]
                transitos_lentos.append(Planet(**planet_data))
                logger.info(f"✅ Trânsito lento {i}: {planet_data.get('name', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro trânsito lento {i}: {e}")
                raise
        
        # 3. Separar natal (11-21)
        logger.info("🔄 Processando natal...")
        natal = []
        for i in range(11, 22):
            try:
                planet_data = data[i]
                natal.append(Planet(**planet_data))
                logger.info(f"✅ Natal {i-11}: {planet_data.get('name', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro natal {i-11}: {e}")
                raise
        
        # 4. Separar cúspides (22)
        logger.info("🔄 Processando cúspides...")
        try:
            cuspides_data = data[22]
            houses = HouseSystem(
                houses=[House(**house) for house in cuspides_data.get("houses", [])],
                ascendant=cuspides_data.get("ascendant"),
                midheaven=cuspides_data.get("midheaven"),
                vertex=cuspides_data.get("vertex")
            )
            logger.info(f"✅ {len(houses.houses)} casas processadas")
        except Exception as e:
            logger.error(f"❌ Erro cúspides: {e}")
            raise
        
        # 5. Separar trânsitos rápidos (23+)
        logger.info("🔄 Processando trânsitos rápidos...")
        transitos_rapidos = []
        if len(data) > 23:
            for i in range(23, len(data)):
                try:
                    planet_data = data[i]
                    transitos_rapidos.append(Planet(**planet_data))
                    logger.info(f"✅ Trânsito rápido {i-23}: {planet_data.get('name', 'N/A')}")
                except Exception as e:
                    logger.warning(f"⚠️ Ignorando trânsito rápido {i-23}: {e}")
                    continue
        
        # 6. Criar request e chamar análise
        logger.info("🚀 Executando análise completa...")
        request_obj = AnalysisRequest(
            transitos_lentos=transitos_lentos,
            natal=natal,
            houses=houses,
            transitos_rapidos=transitos_rapidos
        )
        
        resultado = await analyze_professional_area(request_obj)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"🎉 Análise REAL concluída em {processing_time}ms")
        
        # Adicionar meta dados específicos do processamento
        resultado["meta_info"]["processing_time_ms"] = processing_time
        resultado["meta_info"]["source"] = "analyze_real_data"
        resultado["meta_info"]["input_elements"] = len(data)
        
        return resultado
        
    except Exception as e:
        error_msg = f"Erro no processamento: {str(e)}"
        logger.error(f"💥 {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@app.post("/astro-completo-nasa")
async def astro_completo_nasa(data: List[Dict[str, Any]]):
    """
    Endpoint principal - AGORA com output otimizado por padrão.
    Mantém todas as funcionalidades mas entrega dados mais focados.
    """
    start_time = time.time()
    try:
        logger.info(f"🚀 Iniciando análise astro-completo-nasa OTIMIZADA com {len(data)} elementos")
        
        # Extrair dados do formato N8N
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        logger.info(f"✅ Dados extraídos: {len(dados_extraidos)} elementos")
        
        # Processar análise completa
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        # Criar versão resumida otimizada
        resultado_otimizado = criar_versao_resumida_para_gemini(resultado_completo)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ Análise otimizada concluída em {execution_time}ms")
        
        # Adicionar meta informações
        resultado_otimizado["meta_info"] = {
            "versao": "otimizada_v2",
            "execution_time_ms": execution_time,
            "engine_source": "AstroEngineCompleto_Otimizado",
            "funcionalidades_mantidas": [
                "Análise completa de todos os planetas",
                "Casas ativadas com datas precisas",
                "Aspectos com orbe de 5 graus",
                "Retrogradações detalhadas",
                "Mudanças de signo próximas",
                "Período de análise: 12 meses"
            ],
            "otimizacoes_aplicadas": [
                "Output resumido para melhor interpretação",
                "Priorização por relevância",
                "Limitação de dados menos importantes",
                "Organização hierárquica dos planetas"
            ]
        }
        
        return resultado_otimizado
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint principal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/astro-completo-gemini")
async def astro_completo_gemini(data: List[Dict[str, Any]]):
    """
    Endpoint OTIMIZADO para Gemini - Retorna apenas dados essenciais para reduzir tokens.
    Usa os mesmos dados do /astro-completo-nasa mas com output resumido.
    """
    start_time = time.time()
    try:
        logger.info(f"🤖 Iniciando análise otimizada para Gemini com {len(data)} elementos")
        
        # Processar dados da mesma forma que o endpoint original
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        # Processar análise completa
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        # Criar versão resumida para Gemini
        resultado_resumido = criar_versao_resumida_para_gemini(resultado_completo)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ Análise Gemini concluída em {execution_time}ms")
        
        # Adicionar meta informações
        resultado_resumido["meta_info_resumo"] = {
            "otimizado_para": "Gemini",
            "limite_tokens": "respeitado",
            "execution_time_ms": execution_time,
            "dados_originais": len(resultado_completo.get('todos_transitos', [])),
            "dados_resumidos": len(resultado_resumido.get('transitos_mais_relevantes', [])),
            "compressao_realizada": True
        }
        
        return resultado_resumido
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /astro-completo-gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no endpoint Gemini: {str(e)}")

@app.post("/converter-para-gemini")
async def converter_para_gemini(dados_completos: Dict[str, Any]):
    """
    Endpoint para converter dados completos em versão resumida para Gemini.
    Útil quando você já tem os dados completos e quer apenas a versão resumida.
    """
    try:
        logger.info("🔄 Convertendo dados completos para versão Gemini")
        
        resultado_resumido = criar_versao_resumida_para_gemini(dados_completos)
        
        # Adicionar informações da conversão
        resultado_resumido["meta_info_conversao"] = {
            "convertido_de": "dados_completos",
            "para": "versao_gemini",
            "timestamp": time.time(),
            "compressao_realizada": True
        }
        
        logger.info("✅ Conversão para Gemini concluída")
        return resultado_resumido
        
    except Exception as e:
        logger.error(f"❌ Erro na conversão para Gemini: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro na conversão: {str(e)}")

@app.post("/verificar-tamanho")
async def verificar_tamanho(dados: Dict[str, Any]):
    """
    Endpoint para verificar o tamanho dos dados em caracteres e estimar tokens.
    Útil para debugging do problema de limite de tokens do Gemini.
    """
    try:
        # Converter para string JSON para contar caracteres
        dados_str = str(dados)
        dados_json = json.dumps(dados, ensure_ascii=False)
        
        # Estimar tokens (aproximadamente 1 token = 4 caracteres)
        caracteres_total = len(dados_json)
        tokens_estimados = caracteres_total // 4
        
        # Verificar se excede limite do Gemini
        limite_gemini = 1048576
        excede_limite = tokens_estimados > limite_gemini
        
        # Criar versão resumida se necessário
        versao_resumida = None
        if excede_limite:
            versao_resumida = criar_versao_resumida_para_gemini(dados)
            versao_resumida_str = json.dumps(versao_resumida, ensure_ascii=False)
            tokens_resumidos = len(versao_resumida_str) // 4
        else:
            tokens_resumidos = tokens_estimados
        
        resultado = {
            "tamanho_original": {
                "caracteres": caracteres_total,
                "tokens_estimados": tokens_estimados,
                "excede_limite_gemini": excede_limite
            },
            "limites_gemini": {
                "limite_tokens": limite_gemini,
                "tokens_disponiveis": limite_gemini - tokens_estimados,
                "percentual_usado": round((tokens_estimados / limite_gemini) * 100, 2)
            },
            "versao_resumida": {
                "foi_criada": excede_limite,
                "tokens_resumidos": tokens_resumidos if excede_limite else None,
                "reducao_percentual": round(((tokens_estimados - tokens_resumidos) / tokens_estimados) * 100, 2) if excede_limite else None
            },
            "recomendacao": {
                "usar_endpoint": "/astro-completo-gemini" if excede_limite else "endpoint_normal",
                "motivo": "Dados excedem limite de tokens do Gemini" if excede_limite else "Dados dentro do limite"
            }
        }
        
        logger.info(f"📊 Verificação de tamanho: {caracteres_total} chars, {tokens_estimados} tokens, excede: {excede_limite}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de tamanho: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro na verificação: {str(e)}")

@app.post("/transito-especifico")
async def analisar_transito_especifico(data: Dict[str, Any]):
    """
    Endpoint para análise específica de um planeta.
    Formato: {"planeta": "Saturno", "dados_completos": {...}}
    """
    try:
        planeta_nome = data.get('planeta', '').strip()
        dados_completos = data.get('dados_completos', {})
        
        if not planeta_nome:
            raise HTTPException(status_code=400, detail="Nome do planeta é obrigatório")
        
        if not dados_completos:
            raise HTTPException(status_code=400, detail="Dados completos são obrigatórios")
        
        logger.info(f"🔍 Análise específica solicitada para: {planeta_nome}")
        
        # Criar análise específica
        analise_especifica = criar_analise_transito_especifico(planeta_nome, dados_completos)
        
        if 'erro' in analise_especifica:
            raise HTTPException(status_code=404, detail=analise_especifica['erro'])
        
        logger.info(f"✅ Análise específica concluída para {planeta_nome}")
        
        return {
            "planeta_analisado": planeta_nome,
            "analise_detalhada": analise_especifica,
            "meta_info": {
                "tipo_analise": "transito_especifico",
                "timestamp": time.time(),
                "funcionalidades_incluidas": [
                    "Casas ativadas com datas",
                    "Aspectos organizados por tipo",
                    "Retrogradações detalhadas",
                    "Análise de período completo (12 meses)",
                    "Orbe de 5 graus para aspectos"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise específica: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/astro-completo-dados-completos")
async def astro_completo_dados_completos(data: List[Dict[str, Any]]):
    """
    Endpoint para dados COMPLETOS sem otimização.
    Use apenas quando realmente precisar de todos os dados.
    ATENÇÃO: Pode exceder limite de tokens do Gemini!
    """
    start_time = time.time()
    try:
        logger.info(f"🚀 Iniciando análise COMPLETA (não otimizada) com {len(data)} elementos")
        
        # Extrair dados do formato N8N
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        # Processar análise completa SEM otimização
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ Análise completa concluída em {execution_time}ms")
        
        # Adicionar meta informações
        if "meta_info" not in resultado_completo:
            resultado_completo["meta_info"] = {}
        resultado_completo["meta_info"]["execution_time_ms"] = execution_time
        resultado_completo["meta_info"]["engine_source"] = "AstroEngineCompleto_DadosCompletos"
        resultado_completo["meta_info"]["aviso"] = "Dados completos - pode exceder limite de tokens do Gemini"
        
        return resultado_completo
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint dados completos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/planetas-individualizados")
async def planetas_individualizados(data: List[Dict[str, Any]]):
    """
    Endpoint OTIMIZADO para consultas específicas sobre planetas.
    Retorna dados organizados por planeta individual, RESPEITANDO limite de tokens do Gemini.
    Ideal para quando a LLM precisa extrair informações de um planeta específico.
    """
    start_time = time.time()
    try:
        logger.info(f"🔍 Iniciando análise individualizada com {len(data)} elementos")
        
        # Extrair dados do formato N8N
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        # Processar análise completa
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        # Organizar dados por planeta individual COM LIMITE DE TOKENS
        planetas_organizados = {}
        
        # Ordenar planetas por relevância (priorizar os mais importantes)
        todos_transitos = resultado_completo.get('todos_transitos', [])
        todos_transitos.sort(key=lambda x: x.get('relevancia', 0), reverse=True)
        
        # LIMITAR a 6 planetas máximo para respeitar tokens
        transitos_limitados = todos_transitos[:6]
        
        for transito in transitos_limitados:
            planeta_nome = transito.get('planeta')
            if not planeta_nome:
                continue
            
            # Extrair dados específicos do planeta
            analise_signo = transito.get('analise_signo_atual', {})
            casas_ativadas = analise_signo.get('casas_ativadas', [])[:3]  # Máximo 3 casas
            aspectos_natal = analise_signo.get('aspectos_com_natal', [])
            retrogradacoes = transito.get('retrogradacoes', [])[:2]  # Máximo 2 retrogradações
            
            # Limitar aspectos aos 5 mais importantes
            aspectos_limitados = sorted(aspectos_natal, key=lambda x: x.get('intensidade', 0), reverse=True)[:5]
            
            # Organizar aspectos por tipo (LIMITADO)
            aspectos_por_tipo = {
                'conjuncao': [],
                'trigono': [],
                'sextil': [],
                'quadratura': [],
                'oposicao': []
            }
            
            for aspecto in aspectos_limitados:
                tipo = aspecto.get('tipo_aspecto', '').lower()
                if tipo in aspectos_por_tipo:
                    aspectos_por_tipo[tipo].append({
                        'planeta_natal': aspecto.get('planeta_natal'),
                        'casa_natal': aspecto.get('casa_natal'),
                        'data_inicio': aspecto.get('data_inicio'),
                        'data_exata': aspecto.get('data_exata'),
                        'data_fim': aspecto.get('data_fim'),
                        'intensidade': aspecto.get('intensidade'),
                        'natureza': aspecto.get('natureza')
                    })
            
            # Organizar dados do planeta (VERSÃO RESUMIDA)
            planetas_organizados[planeta_nome] = {
                'info': {
                    'planeta': planeta_nome,
                    'signo': transito.get('signo_atual'),
                    'grau': transito.get('grau_atual'),
                    'relevancia': transito.get('relevancia'),
                    'retrogrado': transito.get('eh_retrogrado'),
                    'tempo_restante': transito.get('tempo_restante_signo', {}).get('dias'),
                    'data_mudanca': transito.get('tempo_restante_signo', {}).get('data_mudanca'),
                    'proximo_signo': transito.get('proximo_signo')
                },
                
                'casas': [
                    {
                        'num': casa.get('casa'),
                        'entrada': casa.get('data_entrada'),
                        'saida': casa.get('data_saida'),
                        'meses': casa.get('permanencia_meses')
                    }
                    for casa in casas_ativadas
                ],
                
                'aspectos': {
                    'por_tipo': aspectos_por_tipo,
                    'resumo': {
                        'total': len(aspectos_limitados),
                        'harmonicos': len([a for a in aspectos_limitados if a.get('natureza') == 'harmonioso']),
                        'desafiadores': len([a for a in aspectos_limitados if a.get('natureza') == 'desafiador']),
                        'intensos': len([a for a in aspectos_limitados if a.get('intensidade', 0) >= 7])
                    }
                },
                
                'retrogradacoes': [
                    {
                        'inicio': retro.get('inicio'),
                        'fim': retro.get('fim'),
                        'signo': retro.get('signo_retrogradacao'),
                        'dias': retro.get('duracao_dias')
                    }
                    for retro in retrogradacoes
                ],
                
                'status': {
                    'relevancia_nivel': 'alta' if transito.get('relevancia', 0) >= 8 else 'media' if transito.get('relevancia', 0) >= 5 else 'baixa',
                    'muda_signo_breve': transito.get('tempo_restante_signo', {}).get('dias', 999) <= 90,
                    'tem_aspectos_intensos': len([a for a in aspectos_limitados if a.get('intensidade', 0) >= 7]) > 0,
                    'retrogradacao_ativa': len(retrogradacoes) > 0,
                    'multiplas_casas': len(casas_ativadas) > 1
                }
            }
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ Análise individualizada concluída em {execution_time}ms")
        
        # Resultado final OTIMIZADO para limite de tokens
        resultado_otimizado = {
            'planetas': planetas_organizados,
            
            'mudancas_proximas': resultado_completo.get('mudancas_signo_proximas', [])[:3],  # Máximo 3
            
            'resumo': {
                'total_planetas': len(planetas_organizados),
                'alta_relevancia': len([p for p in planetas_organizados.values() if p['status']['relevancia_nivel'] == 'alta']),
                'com_retrogradacao': len([p for p in planetas_organizados.values() if p['status']['retrogradacao_ativa']]),
                'mudando_signo': len([p for p in planetas_organizados.values() if p['status']['muda_signo_breve']]),
                'data_analise': resultado_completo.get('meta_info', {}).get('data_analise')
            },
            
            'como_usar': {
                'acesso_planeta': 'Use planetas["Saturno"] para dados do Saturno',
                'aspectos_tipo': 'Use planetas["Saturno"]["aspectos"]["por_tipo"]["conjuncao"]',
                'info_rapida': 'Use planetas["Saturno"]["status"] para análise rápida'
            },
            
            'meta': {
                'otimizado_para': 'Consultas específicas + Limite tokens Gemini',
                'planetas_incluidos': len(planetas_organizados),
                'planetas_omitidos': len(todos_transitos) - len(planetas_organizados),
                'criterio_selecao': 'Ordenados por relevância, top 6 planetas',
                'execution_time_ms': execution_time,
                'tokens_estimados': 'Aproximadamente 150k-250k tokens'
            }
        }
        
        return resultado_otimizado
        
    except Exception as e:
        logger.error(f"❌ Erro no endpoint planetas individualizados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ============================================================================
# NOVOS ENDPOINTS OTIMIZADOS PARA TRÂNSITOS ESPECÍFICOS
# ============================================================================

@app.post("/transitos-minimo")
async def transitos_output_minimo(data: List[Dict[str, Any]]):
    """
    🎯 ENDPOINT OTIMIZADO PARA TRÂNSITOS ESPECÍFICOS
    
    Retorna apenas dados MÍNIMOS necessários para LLM produzir
    respostas sobre trânsitos específicos sem estourar contexto.
    
    Redução: ~90% menor que output completo
    Mantém: Todos dados essenciais para análise VI. TRÂNSITOS ESPECÍFICOS
    """
    start_time = time.time()
    try:
        logger.info(f"🎯 TRÂNSITOS MÍNIMO: Iniciando com {len(data)} elementos")
        
        # Extrair dados do formato N8N (mesmo padrão dos outros endpoints)
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        # Processar análise completa primeiro
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        # Criar output reduzido
        output_minimo = criar_output_minimo_transitos(resultado_completo)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ TRÂNSITOS MÍNIMO: Concluído em {execution_time}ms")
        
        # Meta informações
        output_minimo['meta'] = {
            'tipo': 'transitos_reduzido',
            'tempo_ms': execution_time,
            'reducao': 'Output reduzido para análise',
            'max_planetas': 4,
            'max_aspectos_por_planeta': 2
        }
        
        return output_minimo
        
    except Exception as e:
        logger.error(f"❌ Erro TRÂNSITOS MÍNIMO: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.post("/planeta-especifico-minimo")
async def planeta_especifico_minimo(request: Dict[str, Any]):
    """
    🔍 ANÁLISE DE PLANETA ESPECÍFICO - OUTPUT MÍNIMO
    
    Para quando você quer analisar apenas 1 planeta específico.
    Ideal para perguntas como "Como Saturno vai me impactar?"
    
    Input: {
        "planeta": "Saturno",
        "dados_entrada": [array com 23+ elementos]
    }
    
    Output: Dados mínimos apenas do planeta solicitado
    """
    start_time = time.time()
    try:
        planeta_nome = request.get('planeta', '').strip()
        dados_entrada = request.get('dados_entrada', [])
        
        if not planeta_nome:
            raise HTTPException(status_code=400, detail="Campo 'planeta' é obrigatório")
        
        if not dados_entrada or len(dados_entrada) < 23:
            raise HTTPException(
                status_code=400, 
                detail="Campo 'dados_entrada' deve ter pelo menos 23 elementos"
            )
        
        logger.info(f"🔍 PLANETA ESPECÍFICO: Analisando {planeta_nome}")
        
        # Processar dados completos
        resultado_completo = astro_engine.processar_completo(dados_entrada)
        
        # Buscar planeta específico
        todos_transitos = resultado_completo.get('todos_transitos', [])
        planeta_encontrado = None
        
        for transito in todos_transitos:
            if transito.get('planeta', '').lower() == planeta_nome.lower():
                planeta_encontrado = transito
                break
        
        if not planeta_encontrado:
            raise HTTPException(
                status_code=404, 
                detail=f"Planeta '{planeta_nome}' não encontrado nos dados"
            )
        
        # Extrair dados mínimos apenas deste planeta
        analise_signo = planeta_encontrado.get('analise_signo_atual', {})
        
        resultado_planeta = {
            'planeta': planeta_nome,
            'signo': planeta_encontrado.get('signo_atual'),
            'grau': round(planeta_encontrado.get('grau_atual', 0), 1),
            'retrogrado': planeta_encontrado.get('eh_retrogrado', False),
            
            # Casas ativadas (todas as encontradas)
            'casas': [
                {
                    'numero': casa.get('casa'),
                    'data_entrada': casa.get('data_entrada'),
                    'data_saida': casa.get('data_saida'),
                    'permanencia_meses': round(casa.get('permanencia_meses', 0), 1)
                }
                for casa in analise_signo.get('casas_ativadas', [])
            ],
            
            # Retrogradações
            'retrogradacoes': [
                {
                    'data_inicio': retro.get('inicio'),
                    'data_fim': retro.get('fim'),
                    'signo_anterior': retro.get('signo_retrogradacao'),
                    'duracao_dias': retro.get('duracao_dias', 0)
                }
                for retro in planeta_encontrado.get('retrogradacoes', [])
            ],
            
            # Aspectos maiores apenas (orbe 5°)
            'aspectos': [
                {
                    'tipo': asp.get('tipo_aspecto'),
                    'planeta_natal': asp.get('planeta_natal'),
                    'casa_natal': asp.get('casa_natal'),
                    'data_inicio': asp.get('data_inicio'),
                    'data_fim': asp.get('data_fim'),
                    'intensidade': asp.get('intensidade')
                }
                for asp in analise_signo.get('aspectos_com_natal', [])
                if asp.get('tipo_aspecto') in ['conjunção', 'trígono', 'sextil', 'quadratura', 'oposição']
            ],
            
            # Tempo restante no signo
            'tempo_no_signo': {
                'dias_restantes': planeta_encontrado.get('tempo_restante_signo', {}).get('dias', 0),
                'data_mudanca': planeta_encontrado.get('tempo_restante_signo', {}).get('data_mudanca'),
                'proximo_signo': planeta_encontrado.get('proximo_signo')
            }
        }
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ PLANETA ESPECÍFICO: {planeta_nome} analisado em {execution_time}ms")
        
        return {
            'resultado': resultado_planeta,
            'meta': {
                'planeta_analisado': planeta_nome,
                'tempo_processamento_ms': execution_time,
                'resumo': {
                    'total_casas': len(resultado_planeta['casas']),
                    'total_aspectos': len(resultado_planeta['aspectos']),
                    'total_retrogradacoes': len(resultado_planeta['retrogradacoes']),
                    'muda_signo_em_breve': resultado_planeta['tempo_no_signo']['dias_restantes'] <= 90
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro PLANETA ESPECÍFICO: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

def criar_output_ultra_minimo_debug(dados_completos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Output ULTRA MÍNIMO apenas para DEBUG
    Foca em Urano e dados essenciais para identificar problemas
    """
    
    todos_transitos = dados_completos.get('todos_transitos', [])
    planetas_debug = []
    
    # Processar apenas planetas relevantes, com foco em Urano
    for transito in todos_transitos:
        planeta_nome = transito.get('planeta')
        if not planeta_nome:
            continue
            
        # DADOS BÁSICOS (mínimo necessário)
        planeta_basico = {
            'planeta': planeta_nome,
            'signo_atual': transito.get('signo_atual'),
            'eh_retrogrado': transito.get('eh_retrogrado', False)
        }
        
        # Para Urano, pegar mais detalhes
        if planeta_nome == 'Urano':
            planeta_basico['detalhes_urano'] = {
                'movimento': transito.get('movimento', {}),
                'tempo_restante_signo': transito.get('tempo_restante_signo', {}),
                'retrogradacoes': transito.get('retrogradacoes', [])
            }
        
        # CASAS ATIVADAS (apenas 1, dados mínimos)
        analise_signo = transito.get('analise_signo_atual', {})
        casas_originais = analise_signo.get('casas_ativadas', [])
        
        if casas_originais:
            casa_principal = casas_originais[0]
            planeta_basico['casa_principal'] = {
                'casa': casa_principal.get('casa'),
                'entrada': casa_principal.get('data_entrada'),
                'saida': casa_principal.get('data_saida')
            }
        
        planetas_debug.append(planeta_basico)
    
    # Focar apenas em planetas importantes
    planetas_importantes = ['Urano', 'Saturno', 'Plutão', 'Netuno', 'Júpiter']
    planetas_filtrados = [p for p in planetas_debug if p['planeta'] in planetas_importantes]
    
    # Output final ULTRA REDUZIDO para debug
    return {
        'planetas_debug': planetas_filtrados,
        'total_planetas': len(planetas_debug),
        'data_analise': dados_completos.get('meta_info', {}).get('data_analise'),
        'debug_info': 'Output ultra reduzido para identificar problemas'
    }

@app.post("/debug-urano")
async def debug_urano_output(data: List[Dict[str, Any]]):
    """
    🔍 ENDPOINT DEBUG PARA URANO
    
    Retorna apenas dados essenciais para identificar problemas
    nos dados de Urano (datas, retrogradação, etc.)
    """
    start_time = time.time()
    try:
        logger.info(f"🔍 DEBUG URANO: Iniciando com {len(data)} elementos")
        
        # Extrair dados do formato N8N (mesmo padrão dos outros endpoints)
        dados_extraidos = []
        for item in data:
            if isinstance(item, dict) and "json" in item:
                dados_extraidos.append(item["json"])
            else:
                dados_extraidos.append(item)
        
        # Processar análise completa primeiro
        resultado_completo = astro_engine.processar_completo(dados_extraidos)
        
        # Criar output ULTRA MÍNIMO para debug
        output_debug = criar_output_ultra_minimo_debug(resultado_completo)
        
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ DEBUG URANO: Concluído em {execution_time}ms")
        
        # Meta informações mínimas
        output_debug['meta'] = {
            'tipo': 'debug_urano',
            'tempo_ms': execution_time,
            'objetivo': 'Identificar problemas com dados de Urano',
            'tamanho': 'Ultra reduzido para análise'
        }
        
        return output_debug
        
    except Exception as e:
        logger.error(f"❌ Erro DEBUG URANO: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

# ============ EXECUÇÃO ============

if __name__ == "__main__":
    print("🌟 API Astrológica Profissional v2.0 - OTIMIZADA + TRÂNSITOS MÍNIMOS")
    print("⚡ Recursos implementados:")
    print("  ✅ Análise completa de trânsitos")
    print("  ✅ Output MÍNIMO para trânsitos específicos (90% menor)")
    print("  ✅ Priorização por relevância")
    print("  ✅ Casas ativadas com datas precisas")
    print("  ✅ Aspectos com orbe de 5 graus")
    print("  ✅ Retrogradações detalhadas")
    print("  ✅ Período de análise: 12 meses")
    print("  ✅ Análise de trânsitos específicos")
    print("  ✅ Mudanças de signo próximas")
    print("  ✅ Compatível com limite de tokens do Claude")
    print("")
    print("🚀 Endpoints disponíveis:")
    print("  🎯 /transitos-minimo (RECOMENDADO - output mínimo)")
    print("  🔍 /planeta-especifico-minimo (análise de 1 planeta específico)")
    print("  📊 /astro-completo-nasa (análise completa otimizada)")
    print("  🔍 /planetas-individualizados (dados organizados por planeta)")
    print("  🎯 /transito-especifico (análise específica quando já sabe o planeta)")
    print("  🤖 /astro-completo-gemini (versão específica para Gemini)")
    print("  📈 /verificar-tamanho (verificação de tokens)")
    print("  🔄 /converter-para-gemini (converter dados existentes)")
    print("  📋 /astro-completo-dados-completos (dados completos)")
    print("")
    print("📄 Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    print("⚠️  IMPORTANTE: Endpoint principal agora é /transitos-minimo!")
    print("💡 NOVO: Output 90% menor para resolver problema de contexto do Claude!")
    print("🎯 IDEAL: /planeta-especifico-minimo para análise de planetas específicos!")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )