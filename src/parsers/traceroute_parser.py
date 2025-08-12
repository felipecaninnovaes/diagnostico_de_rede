"""Parser para resultados de traceroute."""

import re
from typing import List, Optional
from datetime import datetime

from ..models.network_test import TracerouteResult, TracerouteHop, TestStatus


class TracerouteParser:
    """Parser para resultados do comando traceroute."""
    
    def __init__(self):
        # Padrão para linha de hop do traceroute
        self.hop_pattern = re.compile(
            r'^\s*(\d+)\s+([\d.]+|\*)\s+([\d.]+|\*)\s+ms'
        )
        self.ip_pattern = re.compile(r'([\d.]+)')
    
    def parse(self, output: str, target: str) -> TracerouteResult:
        """Faz o parse da saída do comando traceroute."""
        try:
            lines = output.strip().split('\n')
            hops = []
            
            for line in lines:
                hop = self._parse_hop_line(line)
                if hop:
                    hops.append(hop)
            
            # Determina status
            status = TestStatus.SUCCESS
            if not hops:
                status = TestStatus.FAILED
            elif len(hops) > 30:  # Muitos hops pode indicar problema
                status = TestStatus.WARNING
            
            return TracerouteResult(
                status=status,
                target=target,
                hops=hops,
                total_hops=len(hops),
                timestamp=datetime.now(),
                raw_output=output
            )
            
        except Exception as e:
            return TracerouteResult(
                status=TestStatus.FAILED,
                target=target,
                hops=[],
                total_hops=0,
                timestamp=datetime.now(),
                raw_output=output,
                error_message=str(e)
            )
    
    def _parse_hop_line(self, line: str) -> Optional[TracerouteHop]:
        """Faz o parse de uma linha de hop do traceroute."""
        try:
            # Remove espaços extras
            line = line.strip()
            
            # Verifica se é uma linha de hop válida
            if not line or line.startswith('traceroute'):
                return None
            
            # Parse básico do número do hop
            parts = line.split()
            if not parts or not parts[0].isdigit():
                return None
            
            hop_number = int(parts[0])
            
            # Procura por IP e tempo
            ip_address = None
            response_time = None
            
            # Procura IP
            ip_match = self.ip_pattern.search(line)
            if ip_match:
                ip_address = ip_match.group(1)
            
            # Procura tempo de resposta
            time_match = re.search(r'([\d.]+)\s*ms', line)
            if time_match:
                response_time = float(time_match.group(1))
            
            # Verifica se há timeout (*)
            is_timeout = '*' in line and response_time is None
            
            return TracerouteHop(
                hop_number=hop_number,
                ip_address=ip_address or '*',
                response_time=response_time or 0.0,
                is_timeout=is_timeout
            )
            
        except Exception:
            return None
