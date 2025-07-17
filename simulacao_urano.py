#!/usr/bin/env python3
"""
Simulação CORRIGIDA para testar os trânsitos específicos
Foco: Urano em Gêmeos e seus impactos com novo endpoint
"""

import sys
import os
sys.path.append('app')

from main import TransitoAstrologicoPreciso
import json
from datetime import datetime

def simular_transitos_especificos():
    """Simula o processamento dos dados com novo endpoint"""
    
    # Dados fornecidos pelo usuário - EXATAMENTE como foram enviados
    dados_entrada = [
        {
            "name": "Sol",
            "fullDegree": 108.53176942939929,
            "normDegree": 18.53176942939929,
            "speed": 0.953297254349973,
            "isRetro": "false",
            "sign": "Câncer",
            "house": 11
        },
        {
            "name": "Lua",
            "fullDegree": 284.77673438287144,
            "normDegree": 14.776734382871439,
            "speed": 12.756643151967362,
            "isRetro": "false",
            "sign": "Capricórnio",
            "house": 4
        },
        {
            "name": "Marte",
            "fullDegree": 163.35001656796734,
            "normDegree": 13.350016567967344,
            "speed": 0.5907905340585999,
            "isRetro": "false",
            "sign": "Virgem",
            "house": 12
        },
        {
            "name": "Mercúrio",
            "fullDegree": 133.30580544564694,
            "normDegree": 13.30580544564694,
            "speed": 0.5738094712183228,
            "isRetro": "false",
            "sign": "Leão",
            "house": 12
        },
        {
            "name": "Júpiter",
            "fullDegree": 96.98008840589952,
            "normDegree": 6.980088405899522,
            "speed": 0.2255083010453907,
            "isRetro": "false",
            "sign": "Câncer",
            "house": 10
        },
        {
            "name": "Vênus",
            "fullDegree": 66.53871244953658,
            "normDegree": 6.538712449536575,
            "speed": 1.1162654168292558,
            "isRetro": "false",
            "sign": "Gémeos",
            "house": 9
        },
        {
            "name": "Saturno",
            "fullDegree": 1.9285631448239395,
            "normDegree": 1.9285631448239395,
            "speed": 0.004447178497415294,
            "isRetro": "false",
            "sign": "Áries",
            "house": 7
        },
        {
            "name": "Urano",
            "fullDegree": 60.1410124933791,
            "normDegree": 0.14101249337910104,
            "speed": 0.04296132052427075,
            "isRetro": "false",
            "sign": "Gémeos",
            "house": 9
        },
        {
            "name": "Netuno",
            "fullDegree": 2.1671114510337413,
            "normDegree": 2.1671114510337413,
            "speed": -0.0029953834342042185,
            "isRetro": "true",
            "sign": "Áries",
            "house": 7
        },
        {
            "name": "Plutão",
            "fullDegree": 302.9321583722748,
            "normDegree": 2.9321583722747846,
            "speed": -0.022580392589534426,
            "isRetro": "true",
            "sign": "Aquário",
            "house": 5
        },
        {
            "name": "Ascendente",
            "fullDegree": 167.41968063929528,
            "normDegree": 17.41968063929528,
            "speed": 0,
            "isRetro": "false",
            "sign": "Virgem",
            "house": 1
        }
    ]
    
    # Dados natais (segunda parte dos dados fornecidos)
    dados_natais = [
        {
            "name": "Sol",
            "fullDegree": 37.17271117342652,
            "normDegree": 7.172711173426521,
            "speed": 0.9728870149550412,
            "isRetro": "false",
            "sign": "Touro",
            "house": 5
        },
        {
            "name": "Lua",
            "fullDegree": 36.18683038327604,
            "normDegree": 6.186830383276039,
            "speed": 12.875229515168789,
            "isRetro": "false",
            "sign": "Touro",
            "house": 5
        },
        {
            "name": "Marte",
            "fullDegree": 74.82850875108164,
            "normDegree": 14.828508751081642,
            "speed": 0.6604282944889841,
            "isRetro": "false",
            "sign": "Gémeos",
            "house": 6
        },
        {
            "name": "Mercúrio",
            "fullDegree": 26.674651503139224,
            "normDegree": 26.674651503139224,
            "speed": 1.9695856539031649,
            "isRetro": "false",
            "sign": "Áries",
            "house": 5
        },
        {
            "name": "Júpiter",
            "fullDegree": 13.446390063746119,
            "normDegree": 13.446390063746119,
            "speed": 0.23134800720651738,
            "isRetro": "false",
            "sign": "Áries",
            "house": 4
        },
        {
            "name": "Vênus",
            "fullDegree": 6.407038953225113,
            "normDegree": 6.407038953225113,
            "speed": 1.20709081366242,
            "isRetro": "false",
            "sign": "Áries",
            "house": 4
        },
        {
            "name": "Saturno",
            "fullDegree": 260.5458859807966,
            "normDegree": 20.545885980796584,
            "speed": -0.04303339484124459,
            "isRetro": "true",
            "sign": "Sagitário",
            "house": 12
        },
        {
            "name": "Urano",
            "fullDegree": 266.4286850817637,
            "normDegree": 26.428685081763717,
            "speed": -0.021686106628380178,
            "isRetro": "true",
            "sign": "Sagitário",
            "house": 12
        },
        {
            "name": "Netuno",
            "fullDegree": 277.91616468683975,
            "normDegree": 7.91616468683975,
            "speed": -0.009533001106756308,
            "isRetro": "true",
            "sign": "Capricórnio",
            "house": 1
        },
        {
            "name": "Plutão",
            "fullDegree": 218.6262046932924,
            "normDegree": 8.626204693292408,
            "speed": -0.028265724718189153,
            "isRetro": "true",
            "sign": "Escorpião",
            "house": 11
        },
        {
            "name": "Ascendente",
            "fullDegree": 266.8181944733416,
            "normDegree": 26.818194473341578,
            "speed": 0,
            "isRetro": "false",
            "sign": "Sagitário",
            "house": 1
        }
    ]
    
    print("🔮 SIMULAÇÃO: Trânsitos Específicos para LLM")
    print("=" * 50)
    
    # Inicializar calculadora
    calc = TransitoAstrologicoPreciso()
    
    print(f"📅 Data de referência: {calc.data_referencia}")
    print(f"🌟 Swiss Ephemeris: {calc.inicializar_swisseph()}")
    print()
    
    # Processar usando o novo método de trânsitos específicos
    print("🚀 PROCESSANDO TRÂNSITOS ESPECÍFICOS...")
    
    # Separar dados CORRETAMENTE
    planetas_transito = []
    planetas_natais = []
    casas_dados = None
    
    # Primeira passagem: separar dados por tipo
    contador_planetas = 0
    for item in dados_entrada:
        if isinstance(item, dict):
            if 'houses' in item:
                casas_dados = item
            elif 'name' in item:
                if contador_planetas < 11:
                    planetas_transito.append(item)
                else:
                    planetas_natais.append(item)
                contador_planetas += 1
    
    casas_natais = casas_dados.get('houses', []) if casas_dados else []
    
    print(f"📊 Planetas em trânsito: {len(planetas_transito)}")
    print(f"📊 Planetas natais: {len(planetas_natais)}")
    print(f"📊 Casas natais: {len(casas_natais)}")
    
    # Processar especificamente Urano
    urano_transito = None
    for planeta in planetas_transito:
        if planeta.get('name') == 'Urano':
            urano_transito = planeta
            break
    
    if urano_transito:
        print()
        print("🔍 ANÁLISE ESPECÍFICA: URANO EM GÊMEOS")
        print("=" * 50)
        
        try:
            urano_resultado = calc.calcular_transito_especifico(
                urano_transito, 
                planetas_natais, 
                casas_natais
            )
            
            print(f"🌍 Planeta: {urano_resultado['planeta']}")
            print(f"📍 Signo atual: {urano_resultado['signo_atual']}")
            print(f"📊 Grau atual: {urano_resultado['grau_atual']}°")
            print(f"🌐 Longitude: {urano_resultado['longitude_atual']}°")
            print(f"📅 Período de análise: {urano_resultado['periodo_analise']['inicio']} → {urano_resultado['periodo_analise']['fim']}")
            
            # Casas ativadas
            if 'casas_ativadas' in urano_resultado:
                print()
                print("🏠 CASAS ATIVADAS:")
                for casa in urano_resultado['casas_ativadas']:
                    print(f"   Casa {casa['casa']}: {casa['data_entrada']} → {casa['data_saida']} ({casa['duracao_dias']} dias)")
            
            # Retrogradação para signo anterior
            if 'retrogradacao_signo_anterior' in urano_resultado:
                retro = urano_resultado['retrogradacao_signo_anterior']
                print()
                print("↩️ RETROGRADAÇÃO PARA SIGNO ANTERIOR:")
                print(f"   Para {retro['signo_destino']}: {retro['data_inicio']} → {retro['data_fim']}")
                print(f"   Duração: {retro['duracao_dias']} dias")
            else:
                print()
                print("↩️ Nenhuma retrogradação para signo anterior")
            
            # Aspectos maiores
            if 'aspectos_maiores' in urano_resultado:
                print()
                print("⭐ ASPECTOS MAIORES:")
                for aspecto in urano_resultado['aspectos_maiores']:
                    print(f"   {aspecto['tipo_aspecto']} com {aspecto['planeta_natal']} (Casa {aspecto['casa_natal']})")
                    for periodo in aspecto['periodos_ativos']:
                        print(f"     📅 {periodo['data_inicio']} → {periodo['data_fim']} ({periodo['duracao_dias']} dias)")
            
            # Interpretação dos dados
            if 'interpretacao_dados' in urano_resultado:
                interp = urano_resultado['interpretacao_dados']
                print()
                print("📝 DADOS PARA INTERPRETAÇÃO:")
                print(f"   Entrada no signo: {interp['entrada_signo']}")
                print(f"   Saída do signo: {interp['saida_signo']}")
                print(f"   Velocidade: {interp['velocidade_planeta']}")
                print(f"   Tipo de trânsito: {interp['tipo_transito']}")
                
                # Verificar se está correto conforme esperado
                esperado_entrada = "07/07"
                esperado_saida = "08/11"
                
                try:
                    entrada_dt = datetime.strptime(interp['entrada_signo'], '%Y-%m-%d')
                    saida_dt = datetime.strptime(interp['saida_signo'], '%Y-%m-%d')
                    
                    entrada_fmt = entrada_dt.strftime('%d/%m')
                    saida_fmt = saida_dt.strftime('%d/%m')
                    
                    print()
                    print("🎯 VALIDAÇÃO COM RESPOSTA ESPERADA:")
                    print(f"   Entrada esperada: {esperado_entrada} | Calculada: {entrada_fmt}")
                    print(f"   Saída esperada: {esperado_saida} | Calculada: {saida_fmt}")
                    
                    if entrada_fmt == esperado_entrada and saida_fmt == esperado_saida:
                        print("✅ RESULTADO CORRETO!")
                    else:
                        print("❌ Resultado difere do esperado")
                        
                except Exception as e:
                    print(f"❌ Erro ao processar datas: {e}")
            
            print()
            print("📄 JSON COMPLETO PARA LLM:")
            print("=" * 30)
            print(json.dumps(urano_resultado, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"❌ Erro ao processar Urano: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Urano não encontrado nos dados de entrada")

if __name__ == "__main__":
    simular_transitos_especificos() 