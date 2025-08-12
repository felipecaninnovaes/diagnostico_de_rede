"""Parser para resultados de MTR."""

import re
from typing import List, Optional
from datetime import datetime

from ..models.network_test import MTRResult, MTRHop, TestStatus


class MTRParser:
    """Parser para resultados do comando MTR."""
    
    def __init__(self):
        # Padrão para linha de hop do MTR
        # HOST: hostname                    Loss%   Snt   Last   Avg  Best  Wrst StDev
        self.hop_pattern = re.compile(
            r'^\s*(\d+)\.\s+([\w\d\.\-\*]+)\s+'
            r'([\d.]+)%\s+(\d+)\s+'
            r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
        )
        self.ip_pattern = re.compile(r'([\d.]+)')
    
    def parse(self, output: str, target: str) -> MTRResult:
        """Faz o parse da saída do comando MTR."""
        try:
            lines = output.strip().split('\n')
            hops = []
            
            for line in lines:
                hop = self._parse_hop_line(line)
                if hop:
                    hops.append(hop)
            
            # Calcula estatísticas agregadas
            total_loss = sum(hop.loss_percent for hop in hops) / len(hops) if hops else 0
            avg_latency = sum(hop.avg_time for hop in hops) / len(hops) if hops else 0
            
            # Determina status
            status = TestStatus.SUCCESS
            if not hops:
                status = TestStatus.FAILED
            elif total_loss > 10:
                status = TestStatus.WARNING
            elif avg_latency > 200:
                status = TestStatus.WARNING
            
            return MTRResult(
                status=status,
                target=target,
                hops=hops,
                total_hops=len(hops),
                total_loss_percent=total_loss,
                avg_latency=avg_latency,
                timestamp=datetime.now(),
                raw_output=output
            )
            
        except Exception as e:
            return MTRResult(
                status=TestStatus.FAILED,
                target=target,
                hops=[],
                total_hops=0,
                total_loss_percent=100.0,
                avg_latency=0.0,
                timestamp=datetime.now(),
                raw_output=output,
                error_message=str(e)
            )
    
    def _parse_hop_line(self, line: str) -> Optional[MTRHop]:
        """Faz o parse de uma linha de hop do MTR."""
        try:
            # Verifica se é linha de cabeçalho ou dados
            if ('HOST:' in line or 'Loss%' in line or 
                line.strip().startswith('Start') or
                not line.strip()):
                return None
            
            # Parse usando regex
            match = self.hop_pattern.match(line)
            if match:
                hop_number = int(match.group(1))
                hostname = match.group(2)
                loss_percent = float(match.group(3))
                sent_packets = int(match.group(4))
                last_time = float(match.group(5))
                avg_time = float(match.group(6))
                best_time = float(match.group(7))
                worst_time = float(match.group(8))
                std_dev = float(match.group(9))
                
                # Extrai IP do hostname se possível
                ip_match = self.ip_pattern.search(hostname)
                ip_address = ip_match.group(1) if ip_match else hostname
                
                return MTRHop(
                    hop_number=hop_number,
                    hostname=hostname,
                    ip_address=ip_address,
                    loss_percent=loss_percent,
                    sent_packets=sent_packets,
                    last_time=last_time,
                    avg_time=avg_time,
                    best_time=best_time,
                    worst_time=worst_time,
                    std_dev=std_dev
                )
            
            # Fallback para formato alternativo
            return self._parse_hop_line_fallback(line)
            
        except Exception:
            return None
    
    def _parse_hop_line_fallback(self, line: str) -> Optional[MTRHop]:
        """Parse alternativo para diferentes formatos de MTR."""
        try:
            parts = line.split()
            if len(parts) < 3:
                return None
            
            # Tenta extrair número do hop
            hop_match = re.match(r'(\d+)', parts[0])
            if not hop_match:
                return None
            
            hop_number = int(hop_match.group(1))
            
            # Procura por hostname/IP
            hostname = parts[1] if len(parts) > 1 else '???'
            
            # Procura por perda de pacotes
            loss_percent = 0.0
            for part in parts:
                if '%' in part:
                    try:
                        loss_percent = float(part.replace('%', ''))
                        break
                    except ValueError:
                        continue
            
            # Procura por tempos
            times = []
            for part in parts:
                try:
                    if '.' in part and part.replace('.', '').isdigit():
                        times.append(float(part))
                except ValueError:
                    continue
            
            avg_time = sum(times) / len(times) if times else 0.0
            
            return MTRHop(
                hop_number=hop_number,
                hostname=hostname,
                ip_address=hostname,
                loss_percent=loss_percent,
                sent_packets=10,  # Default MTR count
                last_time=times[-1] if times else 0.0,
                avg_time=avg_time,
                best_time=min(times) if times else 0.0,
                worst_time=max(times) if times else 0.0,
                std_dev=0.0
            )
            
        except Exception:
            return None
