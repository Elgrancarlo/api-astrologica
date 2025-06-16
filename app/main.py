from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import uvicorn
import time
import logging
from datetime import datetime, timedelta
import math

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
    isRetro: str
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

class AnalysisRequest(BaseModel):
    transitos_lentos: List[Planet]
    natal: List[Planet]
    houses: HouseSystem
    transitos_rapidos: Optional[List[Planet]] = []

# ============ CALCULADORA ASTROLÓGICA AVANÇADA ============

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

@app.post("/analyze-professional")
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
        request = AnalysisRequest(
            transitos_lentos=transitos_lentos,
            natal=natal,
            houses=houses,
            transitos_rapidos=transitos_rapidos
        )
        
        resultado = await analyze_professional_area(request)
        
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
    print("📄 Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
