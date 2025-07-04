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
         
        # Aspectos principais
        self.aspectos = [
            (0, "conjunção", "harmonioso", 10),
            (60, "sextil", "harmonioso", 6),
            (90, "quadratura", "desafiador", 8),
            (120, "trígono", "harmonioso", 7),
            (180, "oposição", "desafiador", 9)
        ]
         
        # Velocidades médias diárias (graus/dia)
        self.velocidades_medias = {
            'Sol': 0.98, 'Lua': 13.2, 'Mercúrio': 1.38, 'Vênus': 1.2, 'Marte': 0.52,
            'Jupiter': 0.08, 'Júpiter': 0.08, 'Saturno': 0.03, 'Urano': 0.01,
            'Netuno': 0.006, 'Plutao': 0.004, 'Plutão': 0.004
        }
        
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
        """Determina tipo de planeta e orbe apropriado"""
        if nome_planeta in self.planetas_pessoais:
            return {"tipo": "pessoal", "orbe": 5}
        elif nome_planeta in self.planetas_transpessoais:
            return {"tipo": "transpessoal", "orbe": 3}
        return {"tipo": "transpessoal", "orbe": 3}
    
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
    
    def encontrar_planeta(self, nome: str, lista: List[Planet]) -> Optional[Planet]:
        """Busca planeta na lista com ou sem acento"""
        nome_normalizado = nome.lower().replace('ú', 'u').replace('ã', 'a')
        
        for planeta in lista:
            planeta_nome = planeta.name.lower().replace('ú', 'u').replace('ã', 'a')
            if planeta_nome == nome_normalizado:
                return planeta
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
    """
    Engine que substitui EXATAMENTE o código JavaScript
    Mantém todas as funcionalidades + dados NASA
    """
    
    def __init__(self):
        try:
            # Carregar dados NASA/JPL
            self.loader = Loader('.')
            self.planets = self.loader('de421.bsp')
            self.ts = self.loader.timescale()
            self.earth = self.planets['earth']
            
            # Mapeamento planetas (exato do JS)
            self.planet_map = {
                'Sol': self.planets['sun'],
                'Lua': self.planets['moon'], 
                'Mercúrio': self.planets['mercury'],
                'Vênus': self.planets['venus'],
                'Marte': self.planets['mars barycenter'],
                'Júpiter': self.planets['jupiter barycenter'],
                'Saturno': self.planets['saturn barycenter'],
                'Urano': self.planets['uranus barycenter'],
                'Netuno': self.planets['neptune barycenter'],
                'Plutão': self.planets['pluto barycenter']
            }
            
            self.signos = ['Áries', 'Touro', 'Gêmeos', 'Câncer', 'Leão', 'Virgem',
                          'Libra', 'Escorpião', 'Sagitário', 'Capricórnio', 'Aquário', 'Peixes']
            
            self.usar_nasa = True
            logger.info("AstroEngine inicializado com dados NASA/JPL")
            
        except Exception as e:
            logger.error(f"Erro ao carregar NASA: {e}")
            self.usar_nasa = False
            logger.warning("Usando dados alternativos")
    
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
    
    def calcular_retrogradacoes_nasa_dinamico(self, nome_planeta, data_inicio_str, periodo_meses=12):
        """CÁLCULO DINÂMICO de retrogradações usando NASA - SEM dados hard-coded"""
        if not self.usar_nasa:
            return self.calcular_retrogradacoes_fallback(nome_planeta, data_inicio_str, periodo_meses)
        
        try:
            planeta_obj = self.planet_map.get(nome_planeta)
            if not planeta_obj:
                return []
            
            # Período de análise
            dt_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            dt_fim = dt_inicio + timedelta(days=periodo_meses * 30)
            
            retrogradacoes = []
            data_atual = dt_inicio
            velocidade_anterior = None
            inicio_retro = None
            em_retrogradacao = False
            
            logger.info(f"Calculando retrogradações NASA para {nome_planeta} de {data_inicio_str}")
            
            # Verificar dia por dia
            while data_atual <= dt_fim:
                try:
                    # Posições para calcular velocidade
                    t_hoje = self.ts.utc(data_atual.year, data_atual.month, data_atual.day)
                    t_amanha = self.ts.utc(data_atual.year, data_atual.month, data_atual.day + 1)
                    
                    # Posições eclípticas
                    pos_hoje = self.earth.at(t_hoje).observe(planeta_obj).ecliptic_latlon()[0].degrees
                    pos_amanha = self.earth.at(t_amanha).observe(planeta_obj).ecliptic_latlon()[0].degrees
                    
                    # Normalizar longitude
                    if pos_hoje < 0: pos_hoje += 360
                    if pos_amanha < 0: pos_amanha += 360
                    
                    # Calcular velocidade diária
                    velocidade = pos_amanha - pos_hoje
                    if velocidade > 180: velocidade -= 360
                    elif velocidade < -180: velocidade += 360
                    
                    # Detectar INÍCIO de retrogradação (velocidade vira negativa)
                    if velocidade < 0 and not em_retrogradacao:
                        inicio_retro = data_atual.strftime('%Y-%m-%d')
                        em_retrogradacao = True
                        logger.info(f"{nome_planeta} inicia retrogradação em {inicio_retro}")
                    
                    # Detectar FIM de retrogradação (velocidade vira positiva)
                    elif velocidade >= 0 and em_retrogradacao:
                        fim_retro = data_atual.strftime('%Y-%m-%d')
                        em_retrogradacao = False
                        
                        if inicio_retro:
                            # Determinar signo da retrogradação
                            signo_retro = self.obter_signo_por_longitude(pos_hoje)
                            duracao = (data_atual - datetime.strptime(inicio_retro, '%Y-%m-%d')).days
                            
                            retrogradacoes.append({
                                'inicio': inicio_retro,
                                'fim': fim_retro,
                                'duracao_dias': duracao,
                                'signo_retrogradacao': signo_retro,
                                'fonte': 'NASA_CALCULADO',
                                'descricao': f"Durante a retrogradação, {nome_planeta} revisitará graus anteriores e pode intensificar temas relacionados ao signo {signo_retro}"
                            })
                            
                            logger.info(f"{nome_planeta} termina retrogradação em {fim_retro} (duração: {duracao} dias)")
                            inicio_retro = None
                    
                    velocidade_anterior = velocidade
                    data_atual += timedelta(days=1)
                    
                except Exception as e:
                    logger.warning(f"Erro ao calcular em {data_atual}: {e}")
                    data_atual += timedelta(days=1)
                    continue
            
            logger.info(f"Encontradas {len(retrogradacoes)} retrogradações para {nome_planeta}")
            return retrogradacoes
            
        except Exception as e:
            logger.error(f"Erro no cálculo NASA de retrogradações: {e}")
            return self.calcular_retrogradacoes_fallback(nome_planeta, data_inicio_str, periodo_meses)
    
    def obter_signo_por_longitude(self, longitude):
        """Converte longitude eclíptica para signo"""
        signo_index = int(longitude // 30)
        return self.signos[signo_index % 12]
    
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
    
    def calcular_retrogradacoes(self, planeta, signo_atual, velocidade):
        """Interface compatível com código original - agora usa NASA dinâmico"""
        nome_planeta = planeta.get('name', '')
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Usar cálculo dinâmico NASA
        return self.calcular_retrogradacoes_nasa_dinamico(nome_planeta, data_hoje, 12)
    
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
        
        # Calcular retrogradações - usar dados reais
        retrogradacoes = self.calcular_retrogradacoes(planeta, planeta.get('sign'), velocidade)
        
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
        
        # Separar dados conforme estrutura fixa - EXATO DO JS
        transitos_atuais = []
        natal = []
        cuspides = None
        
        for index, data in enumerate(inputs):
            # Pular dados vazios
            if not data:
                continue
                
            if index < 11:
                # Primeiros 11: Trânsitos Atuais
                if data.get('name') and data.get('sign'):
                    # Normalizar dados
                    planeta_normalizado = self.normalizar_planeta_data(data)
                    transitos_atuais.append(planeta_normalizado)
                    logger.info(f'Trânsito {index}: {data.get("name")} em {data.get("sign")} (grau {data.get("normDegree", 0):.1f})')
                    
            elif index < 22:
                # Próximos 11: Natal
                if data.get('name') and data.get('sign'):
                    planeta_normalizado = self.normalizar_planeta_data(data)
                    natal.append(planeta_normalizado)
                    logger.info(f'Natal {index - 11}: {data.get("name")} em {data.get("sign")}, casa {data.get("house", 1)}')
                    
            elif index == 22:
                # Índice 22: Cúspides
                if data.get('houses'):
                    cuspides = data
                    logger.info(f'Cúspides encontradas: {len(data.get("houses", []))} casas')
        
        # Validações - EXATAS DO JS
        if not cuspides or not cuspides.get('houses'):
            return {'erro': "Cúspides não encontradas nos inputs"}
        
        if not transitos_atuais:
            return {'erro': "Nenhum trânsito encontrado nos inputs"}
        
        houses_array = cuspides.get('houses', [])
        
        # ANALISAR TODOS OS PLANETAS RELEVANTES - EXATO DO JS
        planetas_relevantes = ['Júpiter', 'Saturno', 'Urano', 'Netuno', 'Plutão', 'Marte', 'Vênus', 'Mercúrio']
        analise_completa = []
        
        for nome_planeta in planetas_relevantes:
            planeta = self.encontrar_planeta(nome_planeta, transitos_atuais)
            
            if planeta:
                logger.info(f"Processando {nome_planeta}...")
                
                try:
                    analise = self.analisar_transito_planeta(planeta, natal, houses_array)
                    analise_completa.append(analise)
                    
                    logger.info(f"{nome_planeta}: Relevância {analise['relevancia']}, {analise['analise_signo_atual']['resumo']['total_aspectos']} aspectos")
                except Exception as error:
                    logger.error(f"Erro ao analisar {nome_planeta}: {error}")
        
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

# Instância global para o novo motor
astro_engine = AstroEngineCompleto()

# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """Endpoint raiz - verificar se API está funcionando"""
    return {
        "message": "🌟 API Astrológica Profissional v2.0",
        "status": "online",
        "features": [
            "Orbes dinâmicos",
            "Cálculo de datas específicas",
            "Análise de mudanças de signo",
            "Projeção de aspectos futuros",
            "Trânsitos profissionais completos"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "astro-microservice-v2",
        "features_count": 15
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
    Endpoint para a análise astrológica completa com dados NASA/JPL.
    Recebe array linear como no N8N original do código JS.
    """
    start_time = time.time()
    try:
        logger.info(f"🚀 Iniciando análise astro-completo-nasa com {len(data)} elementos")
        resultado = astro_engine.processar_completo(data)
        execution_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"✅ Análise astro-completo-nasa concluída em {execution_time}ms")
        
        # Adicionar meta informações de tempo
        if "meta_info" not in resultado:
            resultado["meta_info"] = {}
        resultado["meta_info"]["execution_time_ms"] = execution_time
        resultado["meta_info"]["engine_source"] = "AstroEngineCompleto_NASA"

        return resultado
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /astro-completo-nasa: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno no Astro Completo: {str(e)}")


# ============ EXECUÇÃO ============

if __name__ == "__main__":
    print("🌟 API Astrológica Profissional v2.0")
    print("⚡ Recursos implementados:")
    print("  ✅ Orbes dinâmicos")
    print("  ✅ Cálculo de datas específicas")
    print("  ✅ Análise de mudanças de signo")
    print("  ✅ Projeção de aspectos futuros")
    print("  ✅ Trânsitos profissionais completos")
    print("  ✅ Separação planetas lentos/rápidos")
    print("  ✅ Análise de permanência em signos")
    print("  ✅ Movimento retrógrado/direto")
    print("  ✅ Estrutura igual ao JavaScript")
    print("  ✅ Integração com dados NASA/JPL para precisão")
    print("  ✅ Novo endpoint /astro-completo-nasa")
    print("📄 Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )