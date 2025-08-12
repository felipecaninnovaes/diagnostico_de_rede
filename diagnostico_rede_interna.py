import subprocess
import time
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import re

# === CONFIGURAÇÕES ===
gateway_ip = "10.15.10.1"       # IP do roteador
ip_lan = "10.15.1.21"                    # Outro dispositivo na LAN (opcional)
dns_alvo = "1.1.1.1"             # DNS para teste (Cloudflare)
dns_site = "www.cloudflare.com"  # Domínio a ser resolvido
iperf3_server_ip = "10.15.1.21"          # Ex: "192.168.0.105" (onde o servidor iperf3 está rodando)

logfile = f"log_rede_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log(msg):
    print(msg)
    with open(logfile, "a") as f:
        f.write(msg + "\n")

def run_cmd(desc, cmd):
    log(f"\n--- {desc} ---")
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        log(output)
        return output
    except subprocess.CalledProcessError as e:
        log(f"Erro ao executar: {cmd}\n{e.output}")
        return ""

def testar_dns():
    log(f"\n--- Teste de DNS com dig ({dns_site}) via {dns_alvo} ---")
    dig_cmd = f"dig @{dns_alvo} {dns_site}"
    try:
        output = subprocess.check_output(dig_cmd, shell=True, text=True)
        log(output)
    except Exception as e:
        log(f"Erro no teste DNS (dig): {e}")
        log("Tentando fallback com nslookup...")
        try:
            output = subprocess.check_output(f"nslookup {dns_site} {dns_alvo}", shell=True, text=True)
            log(output)
        except Exception as e:
            log(f"Erro também no nslookup: {e}")

def testar_iperf3():
    if iperf3_server_ip:
        log(f"\n--- Teste de velocidade LAN com iperf3 ({iperf3_server_ip}) ---")
        cmd = f"iperf3 -c {iperf3_server_ip} -t 10"
        try:
            output = subprocess.check_output(cmd, shell=True, text=True)
            log(output)
        except subprocess.CalledProcessError as e:
            log(f"Erro ao executar iperf3: {e.output}")
    else:
        log("⚠️ iperf3 desativado (ip do servidor não configurado).")

def gerar_pdf_resultados(test_results, caminho_saida_pdf="Relatorio_Teste_Rede.pdf"):
    latency_tests = ["Ping loopback", "Ping gateway", "Ping LAN", "Traceroute Google"]
    latencies = [test_results.get(test, {}).get("latência média (ms)", test_results.get(test, {}).get("latência final (ms)", 0)) for test in latency_tests]

    # Gráfico
    plt.figure(figsize=(10, 6))
    bars = plt.bar(latency_tests, latencies, color='skyblue')
    plt.title("Latência Média dos Testes de Conectividade")
    plt.ylabel("Latência (ms)")
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom')
    plt.tight_layout()
    grafico_path = "grafico_latencia.png"
    plt.savefig(grafico_path)
    plt.close()

    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatório de Testes de Rede", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Resultados:", ln=True)
    pdf.set_font("Arial", '', 11)
    for teste, dados in test_results.items():
        linha = f"- {teste}: " + ", ".join([f"{k} = {v}" for k, v in dados.items()])
        pdf.multi_cell(0, 8, linha)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Gráfico de Latência:", ln=True)
    pdf.image(grafico_path, w=180)

    pdf.output(caminho_saida_pdf)
    print(f"[✔] PDF salvo como {caminho_saida_pdf}")

def extrair_resultados_do_log(log_path):
    test_results = {}

    with open(log_path, "r") as f:
        log = f.read()

    # Ping loopback
    match = re.search(r"Ping loopback.*?rtt min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+) ms", log, re.DOTALL)
    if match:
        test_results["Ping loopback"] = {"latência média (ms)": float(match.group(2))}
    else:
        test_results["Ping loopback"] = {"latência média (ms)": 0}

    # Ping gateway
    match = re.search(r"Ping para o gateway.*?rtt min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+) ms", log, re.DOTALL)
    if match:
        test_results["Ping gateway"] = {"latência média (ms)": float(match.group(2))}
    else:
        test_results["Ping gateway"] = {"latência média (ms)": 0}

    # Ping LAN
    match = re.search(r"Ping para outro dispositivo LAN.*?rtt min/avg/max/mdev = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+) ms", log, re.DOTALL)
    if match:
        test_results["Ping LAN"] = {"latência média (ms)": float(match.group(2))}
    else:
        test_results["Ping LAN"] = {"latência média (ms)": 0}

    # Traceroute Google (latência do último salto e perda intermediária)
    traceroute_lines = re.findall(r"^\s*\d+\s+8\.8\.8\.8\s+([\d\.]+) ms\s+([\d\.]+) ms\s+([\d\.]+) ms", log, re.MULTILINE)
    if traceroute_lines:
        tempos = traceroute_lines[-1]
        medias = [float(t) for t in tempos]
        lat_final = sum(medias)/len(medias)
    else:
        lat_final = 0

    # Conta saltos totais e saltos perdidos (* * *)
    saltos = re.findall(r"^\s*\d+\s+.*", log, re.MULTILINE)
    saltos_perdidos = [s for s in saltos if "* * *" in s]
    if saltos:
        perda_pct = round(100 * len(saltos_perdidos) / len(saltos), 1)
    else:
        perda_pct = 0.0

    test_results["Traceroute Google"] = {
        "latência final (ms)": round(lat_final, 2),
        "perda intermediária (%)": perda_pct
    }

    # DNS (tempo de resposta)
    match = re.search(r"Query time: (\d+) msec", log)
    if match:
        test_results["DNS"] = {"tempo de resposta (ms)": int(match.group(1))}
    else:
        test_results["DNS"] = {"tempo de resposta (ms)": 0}

    # iperf3 (bitrate)
    match = re.search(r"\[ *5\].*?0\.00-10\.00.*?sec\s+[\d\.]+ GBytes\s+([\d\.]+) Mbits/sec", log)
    if match:
        test_results["iperf3"] = {"velocidade LAN (Mbits/s)": float(match.group(1))}
    else:
        test_results["iperf3"] = {"velocidade LAN (Mbits/s)": 0}

    # MTR (perda intermediária)
    mtr_blocks = re.findall(r"\s+(\d+\.\d+)%\s+\d+\s", log)
    # print("mtr_blocks encontrados:", mtr_blocks)
    if len(mtr_blocks) > 2:
        intermediarios = [float(p) for p in mtr_blocks[1:-1] if float(p) > 0]
        # print("Intermediários (Loss% > 0):", intermediarios)
        if intermediarios:
            perda_intermediaria = sum(intermediarios) / len(intermediarios)
        else:
            perda_intermediaria = 0.0
        test_results["MTR para 8.8.8.8"] = {"perda intermediária (%)": round(perda_intermediaria, 1)}
    else:
        test_results["MTR para 8.8.8.8"] = {"perda intermediária (%)": 0.0}

    # mtr_start = log.find("--- MTR para 8.8.8.8 ---")
    # if mtr_start != -1:
    #     print("Trecho MTR:")
    #     print(log[mtr_start:mtr_start+1000])  # Mostra os próximos 1000 caracteres

    return test_results

# Exemplo de uso:
# test_results = extrair_resultados_do_log("log_rede_20250720_131756.txt")
# gerar_pdf_resultados(test_results)

def main():
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log(f"# Diagnóstico de Rede - {start_time}")

    # Executa todos os testes e salva no log
    run_cmd("Ping loopback (127.0.0.1)", "ping -c 10 127.0.0.1")
    run_cmd(f"Ping para o gateway ({gateway_ip})", f"ping -c 10 {gateway_ip}")
    if ip_lan:
        run_cmd(f"Ping para outro dispositivo LAN ({ip_lan})", f"ping -c 10 {ip_lan}")
    else:
        log("⚠️ Teste LAN (outro dispositivo) ignorado — IP não definido.")
    run_cmd("Traceroute para 8.8.8.8", "traceroute -n 8.8.8.8")
    log("\n--- Verificando MTR ---")
    mtr_check = subprocess.call("which mtr", shell=True, stdout=subprocess.DEVNULL)
    if mtr_check == 0:
        run_cmd("MTR para 8.8.8.8", "mtr -rw -c 10 8.8.8.8")
    else:
        log("⚠️ MTR não instalado. Execute: sudo apt install mtr")
    testar_dns()
    testar_iperf3()

    # Extrai resultados do log e gera o PDF
    test_results = extrair_resultados_do_log(logfile)
    gerar_pdf_resultados(test_results)

    log(f"\n# Fim dos testes. Resultados salvos em: {logfile}")

if __name__ == "__main__":
    main()
