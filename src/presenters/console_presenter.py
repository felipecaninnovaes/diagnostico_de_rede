"""Presenter para interface console com Rich."""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.layout import Layout
from rich.live import Live

from ..models.test_results import TestResults
from ..models.network_test import NetworkTest, TestStatus
from ..models.isp_info import ISPProvider


class ConsolePresenter:
    """Presenter para apresentação no console usando Rich."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._live: Optional[Live] = None
    
    def show_header(self, title: str = "Diagnóstico de Rede"):
        """Exibe cabeçalho da aplicação."""
        header_text = Text(title, style="bold cyan")
        header_panel = Panel(header_text, title="🌐 Network Diagnostic Tool", border_style="blue")
        self.console.print(header_panel)
        self.console.print()
    
    def show_isp_info(self, isp_info):
        """Exibe informações do ISP detectado."""
        # Mapeia cores por provedor
        provider_colors = {
            ISPProvider.VIVO: "magenta",
            ISPProvider.NETFLEX: "red", 
            ISPProvider.OI: "yellow",
            ISPProvider.TIM: "blue",
            ISPProvider.UNKNOWN: "white"
        }
        
        color = provider_colors.get(isp_info.provider, "white")
        
        # Cria tabela de informações
        table = Table(title="Informações do ISP", border_style=color)
        table.add_column("Campo", style="cyan", width=20)
        table.add_column("Valor", style=color, width=40)
        
        table.add_row("Provedor", isp_info.provider.value)
        table.add_row("IP Público", isp_info.public_ip)
        
        if isp_info.hostname:
            table.add_row("Hostname", isp_info.hostname)
        
        confidence_text = f"{isp_info.confidence_level:.1%}"
        if isp_info.confidence_level >= 0.8:
            confidence_style = "green"
        elif isp_info.confidence_level >= 0.5:
            confidence_style = "yellow"
        else:
            confidence_style = "red"
        
        table.add_row("Confiança", Text(confidence_text, style=confidence_style))
        
        self.console.print(table)
        self.console.print()
    
    def create_progress_bar(self, description: str = "Executando testes") -> Progress:
        """Cria barra de progresso."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        )
        return self._progress
    
    def start_progress(self):
        """Inicia exibição do progresso."""
        if self._progress:
            self._progress.start()
    
    def stop_progress(self):
        """Para exibição do progresso."""
        if self._progress:
            self._progress.stop()
            self._progress = None
    
    def add_progress_task(self, description: str, total: int = 100) -> TaskID:
        """Adiciona tarefa à barra de progresso."""
        if self._progress:
            return self._progress.add_task(description, total=total)
        return TaskID(0)
    
    def update_progress(self, task_id: TaskID, advance: int = 1, description: Optional[str] = None):
        """Atualiza progresso de uma tarefa."""
        if self._progress:
            if description:
                self._progress.update(task_id, advance=advance, description=description)
            else:
                self._progress.advance(task_id, advance)
    
    def show_test_summary(self, test_results: TestResults):
        """Exibe resumo dos testes executados."""
        summary = test_results.summary
        
        # Tabela de resumo
        table = Table(title="Resumo dos Testes", border_style="green")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")
        
        table.add_row("Total de testes", str(summary.total_tests))
        table.add_row("Sucessos", f"[green]{summary.successful_tests}[/green]")
        table.add_row("Avisos", f"[yellow]{summary.warning_tests}[/yellow]")
        table.add_row("Falhas", f"[red]{summary.failed_tests}[/red]")
        table.add_row("Taxa de sucesso", f"[bold]{summary.success_rate:.1%}[/bold]")
        
        self.console.print(table)
        self.console.print()
    
    def show_detailed_results(self, test_results: TestResults):
        """Exibe resultados detalhados dos testes."""
        for i, test in enumerate(test_results.tests, 1):
            self._show_single_test_result(test, i)
    
    def _show_single_test_result(self, test: NetworkTest, test_number: int):
        """Exibe resultado de um teste específico."""
        # Título do teste
        title = f"Teste {test_number}: {test.target}"
        
        # Cria tabela principal
        table = Table(title=title, border_style="blue", show_header=True, header_style="bold cyan")
        table.add_column("Teste", style="cyan", width=12)
        table.add_column("Status", width=10)
        table.add_column("Detalhes", style="white", width=50)
        
        # Ping
        if test.ping_result:
            ping = test.ping_result
            status_style = self._get_status_style(ping.status)
            details = (f"Perda: {ping.packet_loss_percent:.1f}% | "
                      f"Latência: {ping.avg_time:.1f}ms | "
                      f"Pacotes: {ping.packets_received}/{ping.packets_sent}")
            table.add_row("Ping", f"[{status_style}]{ping.status.value}[/{status_style}]", details)
        
        # Traceroute
        if test.traceroute_result:
            tr = test.traceroute_result
            status_style = self._get_status_style(tr.status)
            details = f"Hops: {tr.total_hops}"
            table.add_row("Traceroute", f"[{status_style}]{tr.status.value}[/{status_style}]", details)
        
        # MTR
        if test.mtr_result:
            mtr = test.mtr_result
            status_style = self._get_status_style(mtr.status)
            details = (f"Hops: {mtr.total_hops} | "
                      f"Perda: {mtr.total_loss_percent:.1f}% | "
                      f"Latência: {mtr.avg_latency:.1f}ms")
            table.add_row("MTR", f"[{status_style}]{mtr.status.value}[/{status_style}]", details)
        
        # Speed Test
        if test.speed_test_result:
            speed = test.speed_test_result
            status_style = self._get_status_style(speed.status)
            details = (f"↓ {speed.download_speed:.1f} Mbps | "
                      f"↑ {speed.upload_speed:.1f} Mbps | "
                      f"Ping: {speed.ping_latency:.1f}ms")
            table.add_row("Velocidade", f"[{status_style}]{speed.status.value}[/{status_style}]", details)
        
        self.console.print(table)
        self.console.print()
    
    def _get_status_style(self, status: TestStatus) -> str:
        """Retorna estilo de cor baseado no status."""
        styles = {
            TestStatus.SUCCESS: "green",
            TestStatus.WARNING: "yellow", 
            TestStatus.FAILED: "red"
        }
        return styles.get(status, "white")
    
    def show_ping_table(self, tests: List[NetworkTest]):
        """Exibe tabela resumida de ping."""
        table = Table(title="Resumo Ping", border_style="green")
        table.add_column("Target", style="cyan")
        table.add_column("Status", width=10)
        table.add_column("Perda %", justify="right")
        table.add_column("Min (ms)", justify="right")
        table.add_column("Avg (ms)", justify="right")
        table.add_column("Max (ms)", justify="right")
        
        for test in tests:
            if test.ping_result:
                ping = test.ping_result
                status_style = self._get_status_style(ping.status)
                table.add_row(
                    test.target,
                    f"[{status_style}]{ping.status.value}[/{status_style}]",
                    f"{ping.packet_loss_percent:.1f}",
                    f"{ping.min_time:.1f}",
                    f"{ping.avg_time:.1f}",
                    f"{ping.max_time:.1f}"
                )
        
        self.console.print(table)
        self.console.print()
    
    def show_speed_test_table(self, tests: List[NetworkTest]):
        """Exibe tabela de testes de velocidade."""
        speed_tests = [test for test in tests if test.speed_test_result]
        
        if not speed_tests:
            return
        
        table = Table(title="Teste de Velocidade", border_style="cyan")
        table.add_column("Target", style="cyan")
        table.add_column("Status", width=10)
        table.add_column("Download", justify="right")
        table.add_column("Upload", justify="right")
        table.add_column("Ping (ms)", justify="right")
        table.add_column("Servidor")
        
        for test in speed_tests:
            speed = test.speed_test_result
            status_style = self._get_status_style(speed.status)
            table.add_row(
                test.target,
                f"[{status_style}]{speed.status.value}[/{status_style}]",
                f"{speed.download_speed:.1f} Mbps",
                f"{speed.upload_speed:.1f} Mbps",
                f"{speed.ping_latency:.1f}",
                speed.server_name or "N/A"
            )
        
        self.console.print(table)
        self.console.print()
    
    def show_error(self, message: str, title: str = "Erro"):
        """Exibe mensagem de erro."""
        error_panel = Panel(
            Text(message, style="red"),
            title=f"❌ {title}",
            border_style="red"
        )
        self.console.print(error_panel)
        self.console.print()
    
    def show_warning(self, message: str, title: str = "Aviso"):
        """Exibe mensagem de aviso."""
        warning_panel = Panel(
            Text(message, style="yellow"),
            title=f"⚠️ {title}",
            border_style="yellow"
        )
        self.console.print(warning_panel)
        self.console.print()
    
    def show_success(self, message: str, title: str = "Sucesso"):
        """Exibe mensagem de sucesso."""
        success_panel = Panel(
            Text(message, style="green"),
            title=f"✅ {title}",
            border_style="green"
        )
        self.console.print(success_panel)
        self.console.print()
    
    def show_info(self, message: str, title: str = "Informação"):
        """Exibe mensagem informativa."""
        info_panel = Panel(
            Text(message, style="blue"),
            title=f"ℹ️ {title}",
            border_style="blue"
        )
        self.console.print(info_panel)
        self.console.print()
    
    def clear_screen(self):
        """Limpa a tela."""
        self.console.clear()
    
    def print_separator(self, char: str = "=", length: int = 60):
        """Imprime separador."""
        self.console.print(char * length, style="dim")
