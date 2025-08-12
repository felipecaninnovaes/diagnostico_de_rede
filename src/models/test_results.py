"""Modelos para resultados de testes."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime
from .network_test import PingResult, TracerouteResult, MTRResult, SpeedTestResult, TestStatus
from .isp_info import ISPInfo

if TYPE_CHECKING:
    from .network_test import NetworkTest


@dataclass
class TestSummary:
    """Resumo dos testes executados."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    warning_tests: int
    average_latency: Optional[float]
    total_packet_loss: float
    execution_time: float
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso dos testes."""
        if self.total_tests == 0:
            return 0.0
        return (self.successful_tests / self.total_tests)
    
    @property
    def overall_status(self) -> str:
        """Status geral dos testes."""
        if self.success_rate >= 90:
            return "excellent"
        elif self.success_rate >= 70:
            return "good"
        elif self.success_rate >= 50:
            return "fair"
        else:
            return "poor"


@dataclass
class TestResults:
    """Resultados completos de todos os testes."""
    timestamp: datetime
    isp_info: ISPInfo
    tests: List['NetworkTest'] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """Duração total dos testes em segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def summary(self) -> TestSummary:
        """Resumo dos testes executados."""
        total_tests = len(self.tests)
        successful_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        total_latency = 0.0
        latency_count = 0
        
        for test in self.tests:
            # Verifica o status do teste baseado no ping (principal indicador)
            if test.ping_result:
                if test.ping_result.status == TestStatus.SUCCESS:
                    successful_tests += 1
                    total_latency += test.ping_result.avg_time
                    latency_count += 1
                elif test.ping_result.status == TestStatus.WARNING:
                    warning_tests += 1
                else:
                    failed_tests += 1
            else:
                # Se não há resultado de ping, considera falha
                failed_tests += 1
        
        avg_latency = total_latency / latency_count if latency_count > 0 else 0.0
        
        return TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests, 
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            average_latency=avg_latency,
            total_packet_loss=0.0,  # Calculado separadamente se necessário
            execution_time=0.0      # Calculado separadamente se necessário
        )
        """Resumo dos resultados."""
        total_tests = len(self.ping_results) + len(self.traceroute_results) + len(self.mtr_results)
        if self.speedtest_result:
            total_tests += 1
        
        successful_tests = 0
        total_latency = 0.0
        latency_count = 0
        total_packet_loss = 0.0
        packet_loss_count = 0
        
        # Analisar resultados de ping
        for result in self.ping_results.values():
            if result.is_successful:
                successful_tests += 1
                total_latency += result.latency_avg
                latency_count += 1
            total_packet_loss += result.packet_loss_percent
            packet_loss_count += 1
        
        # Analisar resultados de traceroute
        for result in self.traceroute_results.values():
            if result.final_latency:
                successful_tests += 1
                total_latency += result.final_latency
                latency_count += 1
        
        # Analisar resultados de MTR
        for result in self.mtr_results.values():
            if result.final_latency:
                successful_tests += 1
                total_latency += result.final_latency
                latency_count += 1
        
        # Analisar speedtest
        if self.speedtest_result and self.speedtest_result.download_mbps > 0:
            successful_tests += 1
        
        avg_latency = total_latency / latency_count if latency_count > 0 else None
        avg_packet_loss = total_packet_loss / packet_loss_count if packet_loss_count > 0 else 0.0
        
        return TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=total_tests - successful_tests,
            average_latency=avg_latency,
            total_packet_loss=avg_packet_loss,
            execution_time=self.duration or 0.0
        )
    
    def get_all_targets(self) -> List[str]:
        """Retorna lista de todos os alvos testados."""
        targets = set()
        targets.update(self.ping_results.keys())
        targets.update(self.traceroute_results.keys())
        targets.update(self.mtr_results.keys())
        return sorted(list(targets))
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte os resultados para dicionário."""
        return {
            "isp_info": {
                "provider": self.isp_info.provider_name if self.isp_info else "Unknown",
                "ip": self.isp_info.public_ip if self.isp_info else "Unknown",
                "hostname": self.isp_info.hostname if self.isp_info else None,
                "ip_type": self.isp_info.ip_type.value if self.isp_info else "unknown",
                "confidence": self.isp_info.confidence_score if self.isp_info else 0
            },
            "ping_results": {
                target: {
                    "packets_sent": result.packets_sent,
                    "packets_received": result.packets_received,
                    "packet_loss": result.packet_loss_percent,
                    "latency_avg": result.latency_avg,
                    "latency_min": result.latency_min,
                    "latency_max": result.latency_max
                }
                for target, result in self.ping_results.items()
            },
            "speedtest": {
                "download_mbps": self.speedtest_result.download_mbps if self.speedtest_result else 0,
                "upload_mbps": self.speedtest_result.upload_mbps if self.speedtest_result else 0,
                "ping_ms": self.speedtest_result.ping_ms if self.speedtest_result else 0
            } if self.speedtest_result else None,
            "summary": {
                "total_tests": self.summary.total_tests,
                "successful_tests": self.summary.successful_tests,
                "success_rate": self.summary.success_rate,
                "overall_status": self.summary.overall_status,
                "execution_time": self.summary.execution_time
            },
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
