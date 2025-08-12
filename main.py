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
                    
                    # Calcula total de testes baseado nos targets
                    total_tests = 0
                    for target in valid_targets:
                        if target in ["8.8.8.8", "1.1.1.1"]:
                            total_tests += 4  # ping, traceroute, mtr, speed_test
                        else:
                            total_tests += 3  # ping, traceroute, mtr
                    
                    # Adiciona tarefa principal
                    main_task = self.presenter.add_progress_task(
                        "Executando testes de rede...", 
                        total=total_tests
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
        # Calcula total de testes baseado nos targets
        total_tests = 0
        for target in targets:
            if target in ["8.8.8.8", "1.1.1.1"]:
                total_tests += 4  # ping, traceroute, mtr, speed_test
            else:
                total_tests += 3  # ping, traceroute, mtr

        # Primeira etapa: detecção do ISP
        self.presenter.update_progress(
            task_id,
            advance=0,
            description="Detectando ISP..."
        )
        
        # Detecta ISP primeiro
        isp_info = self.network_service.isp_detector.detect_isp_comprehensive()
        
        # Segunda etapa: execução dos testes
        self.presenter.update_progress(
            task_id,
            advance=0, 
            description="Executando testes de rede..."
        )
        
        # Executa os testes com monitoramento em tempo real
        from datetime import datetime
        from src.models.test_results import TestResults
        
        test_results = TestResults(
            timestamp=datetime.now(),
            isp_info=isp_info,
            tests=[]
        )
        
        completed_tests = 0
        
        # Executa testes para cada target com monitoramento individual
        for i, target in enumerate(targets, 1):
            target_tests = 4 if target in ["8.8.8.8", "1.1.1.1"] else 3
            
            # Inicia teste do target
            self.presenter.update_progress(
                task_id,
                advance=0,
                description=f"Testando {target} ({i}/{len(targets)})..."
            )
            
            # Executa teste com monitoramento de progresso
            network_test = await self._run_single_target_with_progress(
                target, task_id, completed_tests, total_tests
            )
            test_results.tests.append(network_test)
            
            # Atualiza progresso baseado nos testes completados
            completed_tests += target_tests
            self.presenter.update_progress(
                task_id,
                advance=0,
                description=f"Concluído {target} ({completed_tests}/{total_tests})"
            )
        
        # Finaliza o progresso
        self.presenter.update_progress(
            task_id,
            advance=0,
            description="Testes concluídos"
        )
        
        return test_results
    
    async def _run_single_target_with_progress(self, target: str, task_id, base_completed: int, total_tests: int):
        """Executa teste para um target com atualização de progresso por subteste."""
        from datetime import datetime
        from src.models.network_test import NetworkTest
        
        test = NetworkTest(
            target=target,
            timestamp=datetime.now(),
            ping_result=None,
            traceroute_result=None,
            mtr_result=None,
            speed_test_result=None
        )
        
        current_completed = base_completed
        
        try:
            # Teste de Ping
            self.presenter.update_progress(
                task_id,
                advance=0,
                description=f"Ping para {target}... ({current_completed}/{total_tests})"
            )
            
            ping_result = await self.network_service._run_ping_test(target)
            test.ping_result = ping_result
            current_completed += 1
            
            self.presenter.update_progress(
                task_id,
                advance=1,
                description=f"Ping concluído para {target} ({current_completed}/{total_tests})"
            )
            
            # Teste de Traceroute
            self.presenter.update_progress(
                task_id,
                advance=0,
                description=f"Traceroute para {target}... ({current_completed}/{total_tests})"
            )
            
            traceroute_result = await self.network_service._run_traceroute_test(target)
            test.traceroute_result = traceroute_result
            current_completed += 1
            
            self.presenter.update_progress(
                task_id,
                advance=1,
                description=f"Traceroute concluído para {target} ({current_completed}/{total_tests})"
            )
            
            # Teste de MTR
            self.presenter.update_progress(
                task_id,
                advance=0,
                description=f"MTR para {target}... ({current_completed}/{total_tests})"
            )
            
            mtr_result = await self.network_service._run_mtr_test(target)
            test.mtr_result = mtr_result
            current_completed += 1
            
            self.presenter.update_progress(
                task_id,
                advance=1,
                description=f"MTR concluído para {target} ({current_completed}/{total_tests})"
            )
            
            # Teste de velocidade (apenas para targets específicos)
            if target in ["8.8.8.8", "1.1.1.1"]:
                self.presenter.update_progress(
                    task_id,
                    advance=0,
                    description=f"Teste de velocidade para {target}... ({current_completed}/{total_tests})"
                )
                
                try:
                    speed_result = await asyncio.wait_for(
                        self.network_service._run_speed_test(), 
                        timeout=120.0
                    )
                    test.speed_test_result = speed_result
                except (asyncio.TimeoutError, Exception):
                    # Teste de velocidade falhou ou demorou muito - ignora
                    pass
                
                current_completed += 1
                self.presenter.update_progress(
                    task_id,
                    advance=1,
                    description=f"Teste de velocidade concluído para {target} ({current_completed}/{total_tests})"
                )
        
        except Exception as e:
            # Se houver erro, ainda avança o progresso para não travar
            remaining = (4 if target in ["8.8.8.8", "1.1.1.1"] else 3) - (current_completed - base_completed)
            if remaining > 0:
                self.presenter.update_progress(
                    task_id,
                    advance=remaining,
                    description=f"Erro no teste de {target} ({base_completed + (4 if target in ['8.8.8.8', '1.1.1.1'] else 3)}/{total_tests})"
                )
        
        return test
    
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
