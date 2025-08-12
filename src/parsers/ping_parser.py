"""Parser para resultados de ping."""

import re
from typing import Optional
from datetime import datetime

from ..models.network_test import PingResult, TestStatus


class PingParser:
    """Parser para resultados do comando ping."""
    
    def __init__(self):
        # Padrões regex para parsing (português e inglês)
        self.stats_pattern_pt = re.compile(
            r"(\d+) pacotes transmitidos, (\d+) recebidos.*?(\d+\.?\d*)% packet loss"
        )
        self.stats_pattern_en = re.compile(
            r"(\d+) packets transmitted, (\d+) received.*?(\d+\.?\d*)% packet loss"
        )
        self.rtt_pattern = re.compile(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms"
        )
        self.time_pattern = re.compile(r"time=([\d.]+)ms")
    
    def parse(self, output: str, target: str) -> PingResult:
        """Faz o parse da saída do comando ping."""
        try:
            lines = output.strip().split('\n')
            
            # Inicializa resultado
            result = PingResult(
                status=TestStatus.SUCCESS,
                target=target,
                packets_sent=0,
                packets_received=0,
                packet_loss_percent=0.0,
                min_time=0.0,
                avg_time=0.0,
                max_time=0.0,
                mdev_time=0.0,
                timestamp=datetime.now(),
                raw_output=output
            )
            
            # Parse das estatísticas (tenta português primeiro, depois inglês)
            stats_match = self.stats_pattern_pt.search(output)
            if not stats_match:
                stats_match = self.stats_pattern_en.search(output)
                
            if stats_match:
                result.packets_sent = int(stats_match.group(1))
                result.packets_received = int(stats_match.group(2))
                result.packet_loss_percent = float(stats_match.group(3))
            
            # Parse dos tempos RTT
            rtt_match = self.rtt_pattern.search(output)
            if rtt_match:
                result.min_time = float(rtt_match.group(1))
                result.avg_time = float(rtt_match.group(2))
                result.max_time = float(rtt_match.group(3))
                result.mdev_time = float(rtt_match.group(4))
            
            # Determina status baseado nos dados coletados
            if result.packets_sent == 0 and result.avg_time == 0:
                # Nenhum dado coletado - falha total
                result.status = TestStatus.FAILED
            elif result.packet_loss_percent == 100:
                # Perda total de pacotes
                result.status = TestStatus.FAILED
            elif result.packet_loss_percent > 50:
                # Perda significativa
                result.status = TestStatus.WARNING
            else:
                # Funcionando normalmente
                result.status = TestStatus.SUCCESS
            
            return result
            
        except Exception as e:
            return PingResult(
                status=TestStatus.FAILED,
                target=target,
                packets_sent=0,
                packets_received=0,
                packet_loss_percent=100.0,
                min_time=0.0,
                avg_time=0.0,
                max_time=0.0,
                mdev_time=0.0,
                timestamp=datetime.now(),
                raw_output=output,
                error_message=str(e)
            )
