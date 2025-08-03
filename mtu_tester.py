#!/usr/bin/env python3
"""
MTU Tester - Ferramenta para encontrar o MTU ideal
Converte o script bash original para Python com interface moderna
"""

import subprocess
import platform
import argparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text

console = Console()

def mostrar_banner():
    """Exibe um banner de boas-vindas"""
    banner_text = Text("🔧 MTU TESTER 🔧", style="bold cyan")
    subtitle_text = Text("Ferramenta para encontrar o MTU ideal", style="italic blue")
    
    banner_panel = Panel(
        Align.center(f"{banner_text}\n{subtitle_text}"), 
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(banner_panel)
    console.print()

def ping_test(target, packet_size):
    """
    Testa se um pacote de determinado tamanho pode ser enviado sem fragmentação
    
    Args:
        target (str): Endereço IP ou hostname de destino
        packet_size (int): Tamanho do pacote em bytes
    
    Returns:
        bool: True se o pacote foi enviado sem fragmentação, False caso contrário
    """
    try:
        if platform.system().lower() == "windows":
            # Windows: usar -f para "Don't Fragment" e -l para tamanho
            cmd = ["ping", "-n", "1", "-f", "-l", str(packet_size), target]
        else:
            # Linux/Unix: usar -M do para "Don't Fragment" e -s para tamanho
            cmd = ["ping", "-c", "1", "-M", "do", "-s", str(packet_size), target]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def criar_tabela_resultados(testes):
    """Cria uma tabela com os resultados dos testes"""
    table = Table(show_header=True, header_style="bold magenta", width=80)
    table.add_column("📦 Tamanho", style="cyan", width=15)
    table.add_column("📊 Status", style="white", width=20)
    table.add_column("💬 Resultado", style="green", width=25)
    
    for teste in testes[-10:]:  # Mostrar últimos 10 testes
        size, success = teste
        status = "✅ Sucesso" if success else "❌ Fragmentado"
        resultado = "Pacote íntegro" if success else "Fragmentação detectada"
        table.add_row(f"{size} bytes", status, resultado)
    
    return table

def encontrar_mtu_ideal(target="8.8.8.8", min_size=1200, max_size=1500, verbose=False):
    """
    Encontra o MTU ideal usando busca binária
    
    Args:
        target (str): Endereço de destino para teste
        min_size (int): Tamanho mínimo do pacote
        max_size (int): Tamanho máximo do pacote
        verbose (bool): Se deve mostrar todos os testes
    
    Returns:
        tuple: (maior_pacote_sem_fragmentacao, mtu_ideal)
    """
    testes = []
    
    console.print(f"🎯 [bold yellow]Testando MTU ideal para {target}[/bold yellow]")
    console.print(f"📏 Intervalo: {min_size} - {max_size} bytes\n")
    
    # Calcular número total de testes para a barra de progresso
    import math
    total_testes = math.ceil(math.log2(max_size - min_size + 1))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("🔍 Procurando MTU ideal...", total=total_testes)
        teste_num = 0
        
        while min_size <= max_size:
            mid = (min_size + max_size) // 2
            teste_num += 1
            
            progress.update(task, description=f"🔍 Testando pacote {mid} bytes...")
            
            sucesso = ping_test(target, mid)
            testes.append((mid, sucesso))
            
            if verbose:
                status_emoji = "✅" if sucesso else "❌"
                status_text = "OK" if sucesso else "Fragmentado"
                console.print(f"  {status_emoji} Tamanho {mid}: {status_text}")
            
            if sucesso:
                min_size = mid + 1
            else:
                max_size = mid - 1
            
            progress.update(task, advance=1)
    
    # Resultado final
    maior_pacote = max_size
    mtu_ideal = maior_pacote + 28  # 20 bytes IP header + 8 bytes ICMP header
    
    # Mostrar tabela de resultados se verbose
    if verbose and testes:
        console.print("\n")
        console.print(Panel(criar_tabela_resultados(testes), title="📊 Histórico de Testes", border_style="blue"))
    
    return maior_pacote, mtu_ideal

def mostrar_resultado_final(target, maior_pacote, mtu_ideal):
    """Exibe o resultado final de forma organizada"""
    
    # Criar tabela de resultados
    table = Table(show_header=True, header_style="bold green", width=70)
    table.add_column("📋 Métrica", style="cyan", width=30)
    table.add_column("📈 Valor", style="yellow", width=20)
    table.add_column("💡 Descrição", style="white", width=20)
    
    table.add_row("🎯 Destino", target, "Host testado")
    table.add_row("📦 Maior pacote", f"{maior_pacote} bytes", "Sem fragmentação")
    table.add_row("🔧 MTU Ideal", f"{mtu_ideal} bytes", "Recomendado")
    
    console.print("\n")
    console.print(Panel(table, title="✅ Resultado Final", border_style="green"))
    
    # Mostrar comandos para configurar MTU
    console.print("\n🛠️  [bold cyan]Para configurar o MTU:[/bold cyan]")
    
    if platform.system().lower() == "windows":
        console.print(f"   [dim]Windows:[/dim] netsh interface ipv4 set subinterface \"Interface Name\" mtu={mtu_ideal}")
    else:
        console.print(f"   [dim]Linux:[/dim] sudo ip link set dev eth0 mtu {mtu_ideal}")
        console.print(f"   [dim]Temporário:[/dim] sudo ifconfig eth0 mtu {mtu_ideal}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="🔧 MTU Tester - Encontra o MTU ideal para uma conexão",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python mtu_tester.py                          # Teste padrão (8.8.8.8)
  python mtu_tester.py -t google.com            # Testar Google
  python mtu_tester.py -t 1.1.1.1 -v            # Teste verbose
  python mtu_tester.py --min 1000 --max 1600    # Range personalizado
        """
    )
    
    parser.add_argument("-t", "--target", default="8.8.8.8", 
                       help="Destino para teste (IP ou hostname) [padrão: 8.8.8.8]")
    parser.add_argument("--min", type=int, default=1200,
                       help="Tamanho mínimo do pacote [padrão: 1200]")
    parser.add_argument("--max", type=int, default=1500,
                       help="Tamanho máximo do pacote [padrão: 1500]")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Mostrar todos os testes detalhadamente")
    
    args = parser.parse_args()
    
    # Validações
    if args.min >= args.max:
        console.print("[red]❌ Erro: O tamanho mínimo deve ser menor que o máximo[/red]")
        return 1
    
    if args.min < 0 or args.max > 65507:
        console.print("[red]❌ Erro: Tamanhos devem estar entre 0 e 65507 bytes[/red]")
        return 1
    
    try:
        # Mostrar banner
        mostrar_banner()
        
        # Executar teste
        maior_pacote, mtu_ideal = encontrar_mtu_ideal(
            target=args.target,
            min_size=args.min,
            max_size=args.max,
            verbose=args.verbose
        )
        
        # Mostrar resultado
        mostrar_resultado_final(args.target, maior_pacote, mtu_ideal)
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Teste interrompido pelo usuário[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]❌ Erro inesperado: {e}[/red]")
        return 1

if __name__ == "__main__":
    exit(main())
