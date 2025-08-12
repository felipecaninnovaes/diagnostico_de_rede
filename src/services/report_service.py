"""Serviço para geração de relatórios."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict

from ..models.test_results import TestResults
from ..exceptions import ReportGenerationError


class ReportService:
    """Serviço para geração de relatórios de teste de rede."""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_json_report(self, test_results: TestResults, filename: Optional[str] = None) -> str:
        """Gera relatório em formato JSON."""
        try:
            if not filename:
                timestamp = test_results.timestamp.strftime("%Y%m%d_%H%M%S")
                isp_name = test_results.isp_info.provider.value.lower()
                filename = f"network_test_{isp_name}_{timestamp}.json"
            
            filepath = self.output_dir / filename
            
            # Converte para dicionário serializável
            report_data = self._convert_to_serializable(test_results)
            
            # Salva arquivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            return str(filepath)
            
        except Exception as e:
            raise ReportGenerationError("JSON", str(e), e)
    
    def generate_text_report(self, test_results: TestResults, filename: Optional[str] = None) -> str:
        """Gera relatório em formato texto."""
        try:
            if not filename:
                timestamp = test_results.timestamp.strftime("%Y%m%d_%H%M%S")
                isp_name = test_results.isp_info.provider.value.lower()
                filename = f"network_test_{isp_name}_{timestamp}.txt"
            
            filepath = self.output_dir / filename
            
            # Gera conteúdo do relatório
            content = self._generate_text_content(test_results)
            
            # Salva arquivo texto
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(filepath)
            
        except Exception as e:
            raise ReportGenerationError("texto", str(e), e)
    
    def generate_csv_report(self, test_results: TestResults, filename: Optional[str] = None) -> str:
        """Gera relatório em formato CSV."""
        try:
            if not filename:
                timestamp = test_results.timestamp.strftime("%Y%m%d_%H%M%S")
                isp_name = test_results.isp_info.provider.value.lower()
                filename = f"network_test_{isp_name}_{timestamp}.csv"
            
            filepath = self.output_dir / filename
            
            # Gera conteúdo CSV
            content = self._generate_csv_content(test_results)
            
            # Salva arquivo CSV
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(filepath)
            
        except Exception as e:
            raise ReportGenerationError("CSV", str(e), e)
    
    def _convert_to_serializable(self, test_results: TestResults) -> Dict[str, Any]:
        """Converte TestResults para formato serializável."""
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return {k: convert_datetime(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            else:
                return obj
        
        # Converte usando asdict e processa datetimes
        data = asdict(test_results)
        return convert_datetime(data)
    
    def _generate_text_content(self, test_results: TestResults) -> str:
        """Gera conteúdo do relatório em texto."""
        lines = []
        
        # Cabeçalho
        lines.append("=" * 60)
        lines.append("RELATÓRIO DE DIAGNÓSTICO DE REDE")
        lines.append("=" * 60)
        lines.append("")
        
        # Informações gerais
        lines.append(f"Data/Hora: {test_results.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append(f"ISP: {test_results.isp_info.provider.value}")
        lines.append(f"IP Público: {test_results.isp_info.public_ip}")
        if test_results.isp_info.hostname:
            lines.append(f"Hostname: {test_results.isp_info.hostname}")
        lines.append(f"Confiança da Detecção: {test_results.isp_info.confidence_level:.1%}")
        lines.append("")
        
        # Resumo dos testes
        summary = test_results.summary
        lines.append("RESUMO DOS TESTES")
        lines.append("-" * 20)
        lines.append(f"Total de testes: {summary.total_tests}")
        lines.append(f"Sucessos: {summary.successful_tests}")
        lines.append(f"Falhas: {summary.failed_tests}")
        lines.append(f"Avisos: {summary.warning_tests}")
        lines.append(f"Taxa de sucesso: {summary.success_rate:.1%}")
        lines.append("")
        
        # Detalhes dos testes
        for i, test in enumerate(test_results.tests, 1):
            lines.append(f"TESTE {i}: {test.target}")
            lines.append("-" * 30)
            
            # Ping
            if test.ping_result:
                ping = test.ping_result
                lines.append(f"Ping: {ping.status.value}")
                if ping.status.value != "FAILED":
                    lines.append(f"  Pacotes: {ping.packets_sent} enviados, {ping.packets_received} recebidos")
                    lines.append(f"  Perda: {ping.packet_loss_percent:.1f}%")
                    lines.append(f"  Latência: min={ping.min_time:.1f}ms avg={ping.avg_time:.1f}ms max={ping.max_time:.1f}ms")
            
            # Traceroute
            if test.traceroute_result:
                tr = test.traceroute_result
                lines.append(f"Traceroute: {tr.status.value}")
                lines.append(f"  Total de hops: {tr.total_hops}")
            
            # MTR
            if test.mtr_result:
                mtr = test.mtr_result
                lines.append(f"MTR: {mtr.status.value}")
                if mtr.status.value != "FAILED":
                    lines.append(f"  Hops: {mtr.total_hops}")
                    lines.append(f"  Perda média: {mtr.total_loss_percent:.1f}%")
                    lines.append(f"  Latência média: {mtr.avg_latency:.1f}ms")
            
            # Speed Test
            if test.speed_test_result:
                speed = test.speed_test_result
                lines.append(f"Velocidade: {speed.status.value}")
                if speed.status.value != "FAILED":
                    lines.append(f"  Download: {speed.download_speed:.1f} Mbps")
                    lines.append(f"  Upload: {speed.upload_speed:.1f} Mbps")
                    lines.append(f"  Ping: {speed.ping_latency:.1f}ms")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_csv_content(self, test_results: TestResults) -> str:
        """Gera conteúdo do relatório em CSV."""
        lines = []
        
        # Cabeçalho
        headers = [
            "Target", "Ping_Status", "Ping_Loss_%", "Ping_Avg_ms",
            "Traceroute_Status", "Traceroute_Hops", 
            "MTR_Status", "MTR_Loss_%", "MTR_Avg_ms",
            "Speed_Status", "Download_Mbps", "Upload_Mbps", "Speed_Ping_ms"
        ]
        lines.append(",".join(headers))
        
        # Dados dos testes
        for test in test_results.tests:
            row = [test.target]
            
            # Ping
            if test.ping_result:
                ping = test.ping_result
                row.extend([
                    ping.status.value,
                    f"{ping.packet_loss_percent:.1f}",
                    f"{ping.avg_time:.1f}"
                ])
            else:
                row.extend(["N/A", "N/A", "N/A"])
            
            # Traceroute
            if test.traceroute_result:
                tr = test.traceroute_result
                row.extend([tr.status.value, str(tr.total_hops)])
            else:
                row.extend(["N/A", "N/A"])
            
            # MTR
            if test.mtr_result:
                mtr = test.mtr_result
                row.extend([
                    mtr.status.value,
                    f"{mtr.total_loss_percent:.1f}",
                    f"{mtr.avg_latency:.1f}"
                ])
            else:
                row.extend(["N/A", "N/A", "N/A"])
            
            # Speed Test
            if test.speed_test_result:
                speed = test.speed_test_result
                row.extend([
                    speed.status.value,
                    f"{speed.download_speed:.1f}",
                    f"{speed.upload_speed:.1f}",
                    f"{speed.ping_latency:.1f}"
                ])
            else:
                row.extend(["N/A", "N/A", "N/A", "N/A"])
            
            lines.append(",".join(row))
        
        return "\n".join(lines)
    
    def generate_all_reports(self, test_results: TestResults, base_filename: Optional[str] = None) -> Dict[str, str]:
        """Gera todos os tipos de relatório."""
        reports = {}
        
        try:
            # Determina nome base
            if not base_filename:
                timestamp = test_results.timestamp.strftime("%Y%m%d_%H%M%S")
                isp_name = test_results.isp_info.provider.value.lower()
                base_filename = f"network_test_{isp_name}_{timestamp}"
            
            # Gera relatórios
            reports['json'] = self.generate_json_report(test_results, f"{base_filename}.json")
            reports['text'] = self.generate_text_report(test_results, f"{base_filename}.txt")
            reports['csv'] = self.generate_csv_report(test_results, f"{base_filename}.csv")
            
            return reports
            
        except Exception as e:
            raise ReportGenerationError("múltiplos", str(e), e)
