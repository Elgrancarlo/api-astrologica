#!/usr/bin/env python3
"""
Teste de validação com as respostas corretas do cliente
"""

import sys
import os
sys.path.append('app')

from main import TransitoAstrologicoPreciso
from datetime import datetime, timedelta
import json

def testar_dados_cliente():
    """Testa os dados fornecidos pelo cliente"""
    
    calc = TransitoAstrologicoPreciso()
    
    print("🧪 TESTE DE VALIDAÇÃO - DADOS DO CLIENTE")
    print("=" * 50)
    print(f"📅 Data de referência: {calc.data_referencia}")
    print()
    
    # Dados de teste baseados nas respostas corretas do cliente
    dados_teste = {
        'Mercúrio': {
            'signo': 'Leão',
            'retrogradacao_esperada': {'inicio': '18/07', 'fim': '11/08'},
            'planeta_dados': {
                'name': 'Mercúrio',
                'sign': 'Leão',
                'normDegree': 15.0,
                'fullDegree': 135.0,
                'house': 12
            }
        },
        'Saturno': {
            'signo': 'Áries',
            'entrada_esperada': '25/05',
            'retrogradacao_esperada': {'inicio': '01/09'},
            'planeta_dados': {
                'name': 'Saturno',
                'sign': 'Áries',
                'normDegree': 15.0,
                'fullDegree': 15.0,
                'house': 7
            }
        },
        'Urano': {
            'signo': 'Gêmeos',
            'entrada_esperada': '07/07',
            'retrogradacao_esperada': {'inicio': '08/11'},
            'planeta_dados': {
                'name': 'Urano',
                'sign': 'Gêmeos',
                'normDegree': 0.14,
                'fullDegree': 60.14,
                'house': 9
            }
        }
    }
    
    # Testar cada planeta
    for planeta_nome, dados in dados_teste.items():
        print(f"🔍 TESTANDO {planeta_nome.upper()}")
        print("-" * 30)
        
        planeta_dados = dados['planeta_dados']
        signo = dados['signo']
        
        # Testar entrada no signo
        if 'entrada_esperada' in dados:
            entrada_calculada = calc.calcular_entrada_signo_precisa(planeta_nome, signo)
            entrada_esperada = dados['entrada_esperada']
            
            try:
                entrada_dt = datetime.strptime(entrada_calculada, '%Y-%m-%d')
                entrada_fmt = entrada_dt.strftime('%d/%m')
                
                print(f"📅 Entrada no signo:")
                print(f"   Esperada: {entrada_esperada}")
                print(f"   Calculada: {entrada_fmt}")
                print(f"   {'✅ CORRETO' if entrada_fmt == entrada_esperada else '❌ INCORRETO'}")
            except Exception as e:
                print(f"❌ Erro ao processar entrada: {e}")
        
        # Testar retrogradação
        if 'retrogradacao_esperada' in dados:
            retrogradacoes = calc.detectar_retrogradacao_precisa(planeta_nome)
            retro_esperada = dados['retrogradacao_esperada']
            
            print(f"↩️ Retrogradação:")
            if retrogradacoes:
                retro = retrogradacoes[0]
                try:
                    inicio_dt = datetime.strptime(retro['data_inicio'], '%Y-%m-%d')
                    inicio_fmt = inicio_dt.strftime('%d/%m')
                    
                    print(f"   Início esperado: {retro_esperada['inicio']}")
                    print(f"   Início calculado: {inicio_fmt}")
                    print(f"   {'✅ CORRETO' if inicio_fmt == retro_esperada['inicio'] else '❌ INCORRETO'}")
                    
                    if 'fim' in retro_esperada:
                        fim_dt = datetime.strptime(retro['data_fim'], '%Y-%m-%d')
                        fim_fmt = fim_dt.strftime('%d/%m')
                        
                        print(f"   Fim esperado: {retro_esperada['fim']}")
                        print(f"   Fim calculado: {fim_fmt}")
                        print(f"   {'✅ CORRETO' if fim_fmt == retro_esperada['fim'] else '❌ INCORRETO'}")
                    
                except Exception as e:
                    print(f"❌ Erro ao processar retrogradação: {e}")
            else:
                print(f"   ❌ Nenhuma retrogradação detectada")
        
        print()
    
    # Análise detalhada das posições astronômicas
    print("📊 ANÁLISE DETALHADA DAS POSIÇÕES")
    print("=" * 40)
    
    # Verificar posições nas datas específicas
    datas_importantes = [
        ('25/05/2025', 'Entrada de Saturno em Áries'),
        ('07/07/2025', 'Entrada de Urano em Gêmeos'),
        ('18/07/2025', 'Início retrogradação Mercúrio'),
        ('11/08/2025', 'Fim retrogradação Mercúrio'),
        ('01/09/2025', 'Início retrogradação Saturno'),
        ('08/11/2025', 'Início retrogradação Urano')
    ]
    
    for data_str, evento in datas_importantes:
        try:
            data_obj = datetime.strptime(f"{data_str}/2025", '%d/%m/%Y')
            print(f"\n📅 {data_str} - {evento}")
            
            for planeta in ['Mercúrio', 'Saturno', 'Urano']:
                pos = calc.calcular_posicao_planeta_ephem(planeta, data_obj)
                if pos:
                    velocidade = pos.get('velocidade', 0)
                    status = '↩️' if velocidade < 0 else '➡️'
                    print(f"   {planeta}: {pos['signo']} {pos['grau_no_signo']:.1f}° {status}")
        except Exception as e:
            print(f"❌ Erro ao processar {data_str}: {e}")

if __name__ == "__main__":
    testar_dados_cliente() 