from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🌟 API Astrológica",
    description="Microserviço para cálculos astrológicos profissionais",
    version="1.0.0"
)

# Configurar CORS para aceitar requests do n8n
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

class AnalysisRequest(BaseModel):
    transitos_lentos: List[Planet]
    natal: List[Planet]
    houses: HouseSystem
    transitos_rapidos: Optional[List[Planet]] = []

class AspectResult(BaseModel):
    planeta_transito: str
    planeta_natal: str
    tipo_aspecto: str
    natureza: str
    orbe: float
    intensidade: int

class AnalysisResponse(BaseModel):
    transitos_profissionais: List[Dict[str, Any]]
    aspectos_futuros: List[AspectResult]
    jupiter_oportunidades: Optional[Dict[str, Any]]
    meta_info: Dict[str, Any]

# ============ CALCULADORA ============

class AstroCalculator:
    """Calculadora astrológica simplificada"""
    
    # Configuração de orbes por planeta
    PLANET_ORBS = {
        "Sol": 5.0, "Lua": 5.0, "Mercúrio": 5.0, "Vênus": 5.0, "Marte": 5.0,
        "Júpiter": 3.0, "Jupiter": 3.0, "Saturno": 3.0, 
        "Urano": 3.0, "Netuno": 3.0, "Plutão": 3.0, "Plutao": 3.0
    }
    
    # Aspectos principais
    ASPECTS = [
        (0, "conjunção", "harmonioso", 10),
        (60, "sextil", "harmonioso", 6),
        (90, "quadratura", "desafiador", 8),
        (120, "trígono", "harmonioso", 7),
        (180, "oposição", "desafiador", 9)
    ]
    
    def calculate_aspect(self, degree1: float, degree2: float, 
                        planet1: str, planet2: str) -> Optional[AspectResult]:
        """Calcula aspecto entre dois planetas"""
        
        # Calcular diferença angular
        diff = abs(degree1 - degree2)
        if diff > 180:
            diff = 360 - diff
        
        # Determinar orbe máximo
        orb1 = self.PLANET_ORBS.get(planet1, 3.0)
        orb2 = self.PLANET_ORBS.get(planet2, 3.0)
        max_orb = min(orb1, orb2)
        
        # Verificar aspectos
        for exact_angle, aspect_name, nature, intensity in self.ASPECTS:
            current_orb = abs(diff - exact_angle)
            if current_orb <= max_orb:
                return AspectResult(
                    planeta_transito=planet1,
                    planeta_natal=planet2,
                    tipo_aspecto=aspect_name,
                    natureza=nature,
                    orbe=round(current_orb, 2),
                    intensidade=intensity
                )
        
        return None
    
    def find_professional_transits(self, planets: List[Planet]) -> List[Dict[str, Any]]:
        """Encontra planetas nas casas profissionais (2, 6, 10)"""
        professional_houses = [2, 6, 10]
        transits = []
        
        relevance_map = {
            2: "recursos_financeiros",
            6: "trabalho_rotina", 
            10: "carreira_status"
        }
        
        for planet in planets:
            if planet.house in professional_houses:
                transits.append({
                    "planeta": planet.name,
                    "casa": planet.house,
                    "signo": planet.sign,
                    "grau_atual": round(planet.normDegree, 1),
                    "relevancia": relevance_map[planet.house],
                    "velocidade": abs(planet.speed)
                })
        
        return transits
    
    def analyze_jupiter(self, planets: List[Planet]) -> Optional[Dict[str, Any]]:
        """Análise específica de Júpiter"""
        jupiter = None
        for planet in planets:
            if planet.name.lower() in ['jupiter', 'júpiter']:
                jupiter = planet
                break
        
        if not jupiter:
            return None
        
        opportunities = {
            1: "Expansão da identidade profissional, liderança pessoal",
            2: "Expansão financeira, novos recursos, oportunidades de renda",
            3: "Comunicação expandida, parcerias locais", 
            4: "Base sólida para carreira, trabalho em casa, negócios familiares",
            5: "Criatividade profissional, projetos inovadores",
            6: "Melhoria nas condições de trabalho, expansão da rotina",
            7: "Parcerias profissionais, sociedades, contratos importantes",
            8: "Transformação profissional, recursos compartilhados",
            9: "Expansão internacional, educação superior, publicações",
            10: "Grandes oportunidades de carreira, reconhecimento público",
            11: "Networking poderoso, projetos em grupo",
            12: "Trabalho nos bastidores, projetos espirituais"
        }
        
        return {
            "signo_atual": jupiter.sign,
            "grau_atual": round(jupiter.normDegree, 1),
            "casa_atual": jupiter.house,
            "oportunidade_principal": opportunities.get(jupiter.house, "Casa não mapeada"),
            "velocidade_diaria": abs(jupiter.speed)
        }

# Instância global
calc = AstroCalculator()

# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """Endpoint raiz - verificar se API está funcionando"""
    return {
        "message": "🌟 API Astrológica funcionando!",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "astro-microservice"
    }

@app.post("/analyze-professional", response_model=AnalysisResponse)
async def analyze_professional_area(request: AnalysisRequest):
    """
    Endpoint principal - Análise da área profissional
    
    Analisa trânsitos planetários e aspectos para área profissional
    """
    start_time = time.time()
    
    try:
        logger.info(f"Iniciando análise com {len(request.transitos_lentos)} planetas lentos")
        
        # Combinar todos os planetas para análise
        all_planets = request.transitos_lentos + (request.transitos_rapidos or [])
        
        # 1. Encontrar trânsitos profissionais
        professional_transits = calc.find_professional_transits(all_planets)
        
        # 2. Calcular aspectos entre trânsitos e natal
        aspects = []
        for transit in request.transitos_lentos[:5]:  # Limitar para performance
            for natal in request.natal[:5]:  # Limitar para performance
                aspect = calc.calculate_aspect(
                    transit.fullDegree, 
                    natal.fullDegree,
                    transit.name,
                    natal.name
                )
                if aspect:
                    aspects.append(aspect)
        
        # 3. Análise de Júpiter
        jupiter_analysis = calc.analyze_jupiter(request.transitos_lentos)
        
        # 4. Metadados
        execution_time = round((time.time() - start_time) * 1000, 2)
        
        result = AnalysisResponse(
            transitos_profissionais=professional_transits,
            aspectos_futuros=aspects[:20],  # Limitar resposta
            jupiter_oportunidades=jupiter_analysis,
            meta_info={
                "execution_time_ms": execution_time,
                "total_aspects": len(aspects),
                "professional_transits": len(professional_transits),
                "engine": "python_fastapi",
                "timestamp": time.time()
            }
        )
        
        logger.info(f"Análise concluída em {execution_time}ms")
        return result
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/test-connection")
async def test_connection(data: Dict[str, Any]):
    """Endpoint para testar conexão com n8n"""
    return {
        "message": "Conexão funcionando!",
        "received_keys": list(data.keys()),
        "timestamp": time.time()
    }

@app.post("/analyze-real-data")
async def analyze_real_data(data: List[Dict[str, Any]]):
    """Endpoint para análise de dados reais no formato array"""
    try:
        logger.info(f"📊 Dados recebidos: {len(data)} elementos")
        
        # Log dos primeiros elementos para debug
        for i in range(min(3, len(data))):
            logger.info(f"Elemento {i}: {data[i]}")
        
        # 1. Verificar se temos dados suficientes
        if len(data) < 23:
            raise ValueError(f"Array muito pequeno. Recebido: {len(data)}, esperado: pelo menos 23")
        
        # 2. Separar trânsitos lentos (0-10)
        logger.info("🔄 Separando trânsitos lentos...")
        transitos_lentos_raw = data[0:11]
        transitos_lentos = []
        for i, planet in enumerate(transitos_lentos_raw):
            try:
                transitos_lentos.append(Planet(**planet))
                logger.info(f"✅ Trânsito lento {i}: {planet.get('name', 'sem nome')}")
            except Exception as e:
                logger.error(f"❌ Erro no trânsito lento {i}: {e}")
                raise
        
        # 3. Separar natal (11-21)
        logger.info("🔄 Separando natal...")
        natal_raw = data[11:22]
        natal = []
        for i, planet in enumerate(natal_raw):
            try:
                natal.append(Planet(**planet))
                logger.info(f"✅ Natal {i}: {planet.get('name', 'sem nome')}")
            except Exception as e:
                logger.error(f"❌ Erro no natal {i}: {e}")
                raise
        
        # 4. Separar cúspides (posição 22)
        logger.info("🔄 Separando cúspides...")
        cuspides_raw = data[22]
        logger.info(f"📍 Cúspides raw: {cuspides_raw}")
        
        try:
            houses = HouseSystem(
                houses=[House(**house) for house in cuspides_raw.get("houses", [])],
                ascendant=cuspides_raw.get("ascendant"),
                midheaven=cuspides_raw.get("midheaven"),
                vertex=cuspides_raw.get("vertex")
            )
            logger.info(f"✅ Houses criado com {len(houses.houses)} casas")
        except Exception as e:
            logger.error(f"❌ Erro nas cúspides: {e}")
            raise
        
        # 5. Separar trânsitos rápidos (23+)
        logger.info("🔄 Separando trânsitos rápidos...")
        transitos_rapidos = []
        if len(data) > 23:
            transitos_rapidos_raw = data[23:]
            for i, planet in enumerate(transitos_rapidos_raw):
                try:
                    transitos_rapidos.append(Planet(**planet))
                    logger.info(f"✅ Trânsito rápido {i}: {planet.get('name', 'sem nome')}")
                except Exception as e:
                    logger.error(f"❌ Erro no trânsito rápido {i}: {e}")
                    # Não parar por trânsitos rápidos
                    continue
        
        # 6. Criar request
        logger.info("🔄 Criando request...")
        request = AnalysisRequest(
            transitos_lentos=transitos_lentos,
            natal=natal,
            houses=houses,
            transitos_rapidos=transitos_rapidos
        )
        logger.info("✅ Request criado com sucesso")
        
        # 7. Chamar análise
        logger.info("🔄 Iniciando análise...")
        result = await analyze_professional_area(request)
        logger.info("✅ Análise concluída com sucesso")
        
        return result
        
    except Exception as e:
        error_msg = f"Erro ao processar dados: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"📊 Dados recebidos: {len(data) if 'data' in locals() else 'N/A'} elementos")
        raise HTTPException(status_code=400, detail=error_msg)

# ============ EXECUÇÃO ============

if __name__ == "__main__":
    print("🚀 Iniciando API Astrológica...")
    print("📄 Documentação: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
