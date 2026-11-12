from app.dominio.emocao import EMOCOES_PT
from app.nucleo.criptografia.padrao.aes_gcm import criptografar_aes
from app.nucleo.criptografia.autoral.mce import aplicar_mce
from app.nucleo.criptografia.criptografia_analise import CriptografiaAnalise
import sys
import os
import time
import statistics
import json
import matplotlib.pyplot as plt

# Adiciona o diretório backend ao sys.path para conseguir importar os módulos do app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa as implementações do seu projeto (ajustando para a estrutura atual)


def gerar_dados_ficticios(num_frames=300):
    """Gera uma estrutura de dados de emoções (300 frames = 1 minuto a 5 FPS)"""
    probabilidades = {emocao: 1.0 / len(EMOCOES_PT) for emocao in EMOCOES_PT}
    linha_do_tempo = {
        emocao: [1.0 / len(EMOCOES_PT)] * num_frames for emocao in EMOCOES_PT}

    return {
        "probabilidades": probabilidades,
        "linha_do_tempo": linha_do_tempo
    }


def executar_benchmark(iteracoes=1000):
    print(f"Iniciando benchmark com {iteracoes} iterações...")

    chave_aes = "TESTE_CHAVE_AES_256_MUITO_SEGURA_32B"
    chave_mce_str = "TESTE_CHAVE_MCE_2026"
    chave_mce_bytes = chave_mce_str.encode("utf-8")

    dados = gerar_dados_ficticios(300)  # Simula 1 minuto de vídeo

    # Aquecimento
    for _ in range(10):
        aplicar_mce(dados, chave_mce_bytes)

    # 1. Medir apenas MCE
    tempos_mce = []
    for _ in range(iteracoes):
        inicio = time.perf_counter()
        aplicar_mce(dados, chave_mce_bytes)
        fim = time.perf_counter()
        tempos_mce.append((fim - inicio) * 1000)  # Em milissegundos

    mediana_mce = statistics.median(tempos_mce)
    media_mce = statistics.mean(tempos_mce)
    min_mce = min(tempos_mce)
    max_mce = max(tempos_mce)

    # Obter os dados serializados para testar apenas o AES
    dados_mce = aplicar_mce(dados, chave_mce_bytes)
    texto_mce = json.dumps(dados_mce, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    associado = b"emotionlens:v1"

    # 2. Medir apenas AES-256-GCM
    from app.nucleo.criptografia.padrao.aes_gcm import normalizar_chave_aes
    chave_aes_bytes = normalizar_chave_aes(chave_aes)

    tempos_aes = []
    for _ in range(iteracoes):
        inicio = time.perf_counter()
        criptografar_aes(texto_mce, chave_aes_bytes, associado)
        fim = time.perf_counter()
        tempos_aes.append((fim - inicio) * 1000)

    mediana_aes = statistics.median(tempos_aes)
    media_aes = statistics.mean(tempos_aes)
    min_aes = min(tempos_aes)
    max_aes = max(tempos_aes)

    # 3. Medir Fluxo Completo usando a classe CriptografiaAnalise
    cripto_completa = CriptografiaAnalise(chave_aes, chave_mce_str)
    tempos_completo = []
    for _ in range(iteracoes):
        inicio = time.perf_counter()
        cripto_completa.criptografar(dados)
        fim = time.perf_counter()
        tempos_completo.append((fim - inicio) * 1000)

    mediana_completo = statistics.median(tempos_completo)
    media_completo = statistics.mean(tempos_completo)
    min_completo = min(tempos_completo)
    max_completo = max(tempos_completo)

    print("\n--- RESULTADOS PARA O QUADRO 6 (Tempos de Processamento) ---")
    print(f"| Operação | Repetições | Média (ms) | Mediana (ms) | Mínimo (ms) | Máximo (ms) |")
    print(f"|---|---|---|---|---|---|")
    print(
        f"| MCE (Camada Autoral) | {iteracoes} | {media_mce:.4f} | {mediana_mce:.4f} | {min_mce:.4f} | {max_mce:.4f} |")
    print(
        f"| AES-256-GCM Isolado | {iteracoes} | {media_aes:.4f} | {mediana_aes:.4f} | {min_aes:.4f} | {max_aes:.4f} |")
    print(
        f"| Fluxo Completo (MCE + JSON + AES) | {iteracoes} | {media_completo:.4f} | {mediana_completo:.4f} | {min_completo:.4f} | {max_completo:.4f} |")

    # Gerar o gráfico real
    labels = ['MCE (Camada Autoral)', 'AES-256-GCM', 'Fluxo Completo']
    medianas_ms = [mediana_mce, mediana_aes, mediana_completo]

    fig, ax = plt.subplots(figsize=(8, 6))
    # Usando tons de azul profissional em vez de roxo
    cores = ['#2980b9', '#3498db', '#1abc9c']
    bars = ax.bar(labels, medianas_ms, color=cores, width=0.5)

    ax.set_yscale('log')
    ax.set_ylabel('Tempo (ms) - escala logarítmica', fontsize=11)
    ax.set_title('Comparação do tempo mediano de criptografia',
                 fontsize=12, fontweight='bold', pad=20)

    for bar in bars:
        yval = bar.get_height()
        posicao_texto_y = yval * 1.15
        ax.text(bar.get_x() + bar.get_width()/2, posicao_texto_y,
                f'{yval:.4f} ms',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='-', alpha=0.3, color='gray')
    ax.set_axisbelow(True)

    plt.subplots_adjust(bottom=0.05)

    output_path = os.path.join(os.path.dirname(__file__), "grafico_real.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nGráfico real salvo em: {output_path}")


if __name__ == "__main__":
    executar_benchmark(1000)
