#!/usr/bin/env python3
"""
Script principal CLI para diagnóstico de rede refatorado.

Este script utiliza a nova arquitetura limpa implementada.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import ConfigManager
from src.services import NetworkTestService, ReportService
from src.presenters import ConsolePresenter
from src.models.test_results import TestResults
from src.utils import (
    setup_logger, 
    validate_targets, 
    LogContext,
    default_logger
)
from src.exceptions import NetworkDiagnosticException


class NetworkDiagnosticCLI:
    """Interface CLI principal para diagnóstico de rede."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.network_service = NetworkTestService()
        self.report_service = ReportService()
        self.presenter = ConsolePresenter()
        self.logger = default_logger
    
    async def run(self, args):
        """Executa o diagnóstico de rede."""
        try:
            # Configura targets
            targets = self._get_targets(args)
            
            # Valida targets
            valid_targets, errors = validate_targets(targets)
            if errors:
                for error in errors:
                    self.presenter.show_error(error)
                return 1
            
            # Exibe cabeçalho
            self.presenter.show_header()
            
            # Configura progresso
            if self.config.get_ui_settings().show_progress:
                progress = self.presenter.create_progress_bar()
                with progress:
                    self.presenter.start_progress()
                    
                    # Adiciona tarefa principal
                    main_task = self.presenter.add_progress_task(
                        "Executando testes de rede...", 
                        total=len(valid_targets) * 4  # 4 testes por target
                    )
                    
                    # Executa testes com atualização incremental do progresso
                    test_results = await self._run_tests_with_progress(
                        valid_targets, main_task
                    )
                    
                    self.presenter.stop_progress()
            else:
                # Executa sem barra de progresso
                test_results = await self.network_service.run_comprehensive_test(valid_targets)
            
            # Exibe informações do ISP
            self.presenter.show_isp_info(test_results.isp_info)
            
            # Exibe resultados
            if args.summary_only:
                self.presenter.show_test_summary(test_results)
                self.presenter.show_ping_table(test_results.tests)
                self.presenter.show_speed_test_table(test_results.tests)
            else:
                self.presenter.show_test_summary(test_results)
                self.presenter.show_detailed_results(test_results)
            
            # Gera relatórios se solicitado
            if args.generate_reports:
                await self._generate_reports(test_results, args)
            
            return 0
            
        except NetworkDiagnosticException as e:
            self.presenter.show_error(str(e), "Erro de Diagnóstico")
            self.logger.error(f"Erro de diagnóstico: {e}")
            return 1
        except KeyboardInterrupt:
            self.presenter.show_warning("Operação cancelada pelo usuário")
            return 130
        except Exception as e:
            self.presenter.show_error(f"Erro inesperado: {str(e)}", "Erro Interno")
            self.logger.exception("Erro inesperado")
            return 1
    
    def _get_targets(self, args) -> List[str]:
        """Obtém lista de targets a partir dos argumentos."""
        if args.targets:
            return args.targets
        elif args.target_file:
            return self._load_targets_from_file(args.target_file)
        else:
            return self.config.get_default_targets()
    
    def _load_targets_from_file(self, file_path: str) -> List[str]:
        """Carrega targets de um arquivo."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                targets = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        targets.append(line)
                return targets
        except Exception as e:
            raise NetworkDiagnosticException(f"Erro ao carregar targets do arquivo: {e}")
    
    async def _run_tests_with_progress(self, targets: List[str], task_id) -> TestResults:
        """Executa testes com atualização de progresso por subteste/target."""
        # Estratégia: rodar os testes e, em paralelo, fazer polling do progresso
        # assumindo 4 subtestes por target.
        total_subtests = len(targets) * 4

        async def run_tests():
            return await self.network_service.run_comprehensive_test(targets)

        async def poll_progress():
            completed_prev = 0
            while True:
                completed = 0
                for t in targets:
                    p = self.network_service.get_test_progress(t)
                    if p:
                        completed += int(p.get("completed", 0))
                # Garante não regredir
                if completed > completed_prev:
                    delta = completed - completed_prev
                    completed_prev = completed
                    self.presenter.update_progress(
                        task_id,
                        advance=delta,
                        description=f"Executando testes de rede... ({completed}/{total_subtests})"
                    )
                await asyncio.sleep(0.2)

        tests_task = asyncio.create_task(run_tests())
        poll_task = asyncio.create_task(poll_progress())

        try:
            result = await tests_task
            return result
        finally:
            poll_task.cancel()
            # Finaliza somente atualizando a descrição, sem avançar além do acumulado
            self.presenter.update_progress(task_id, advance=0, description="Testes concluídos")
    
    async def _generate_reports(self, test_results, args):
        """Gera relatórios dos testes."""
        with LogContext(self.logger, "geração de relatórios"):
            try:
                if args.output_dir:
                    self.report_service.output_dir = Path(args.output_dir)
                
                # Gera relatórios conforme formato solicitado
                if args.report_format == "all":
                    reports = self.report_service.generate_all_reports(test_results)
                    for format_type, file_path in reports.items():
                        self.presenter.show_success(
                            f"Relatório {format_type.upper()} gerado: {file_path}"
                        )
                else:
                    if args.report_format == "json":
                        file_path = self.report_service.generate_json_report(test_results)
                    elif args.report_format == "text":
                        file_path = self.report_service.generate_text_report(test_results)
                    elif args.report_format == "csv":
                        file_path = self.report_service.generate_csv_report(test_results)
                    
                    self.presenter.show_success(f"Relatório gerado: {file_path}")
                    
            except Exception as e:
                self.presenter.show_error(f"Erro ao gerar relatórios: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Diagnóstico abrangente de rede com detecção de ISP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                                    # Executa com targets padrão
  %(prog)s -t 8.8.8.8 1.1.1.1                # Testa targets específicos
  %(prog)s -f targets.txt                     # Carrega targets de arquivo
  %(prog)s --summary-only                     # Mostra apenas resumo
  %(prog)s --generate-reports --format json   # Gera relatório JSON
  %(prog)s --output-dir ./reports             # Define diretório de saída
        """
    )
    
    # Argumentos de targets
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "-t", "--targets",
        nargs="+",
        help="Lista de IPs/hostnames para testar"
    )
    target_group.add_argument(
        "-f", "--target-file",
        help="Arquivo contendo lista de targets (um por linha)"
    )
    
    # Argumentos de exibição
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Mostra apenas resumo dos testes"
    )
    
    # Argumentos de relatório
    parser.add_argument(
        "--generate-reports",
        action="store_true", 
        help="Gera relatórios dos testes"
    )
    parser.add_argument(
        "--format",
        dest="report_format",
        choices=["json", "text", "csv", "all"],
        default="all",
        help="Formato do relatório (padrão: all)"
    )
    parser.add_argument(
        "--output-dir",
        help="Diretório para salvar relatórios (padrão: ./reports)"
    )
    
    # Argumentos de configuração
    parser.add_argument(
        "--config",
        help="Caminho para arquivo de configuração personalizado"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nível de log (padrão: INFO)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desabilita cores na saída"
    )
    
    return parser


async def main():
    """Função principal."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configura logging
    logger = setup_logger(
        level=args.log_level,
        use_colors=not args.no_color
    )
    
    # Cria e executa CLI
    cli = NetworkDiagnosticCLI()
    
    # Carrega configuração personalizada se especificada
    if args.config:
        cli.config = ConfigManager(args.config)
    
    # Executa diagnóstico
    exit_code = await cli.run(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    # Executa a aplicação
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)
