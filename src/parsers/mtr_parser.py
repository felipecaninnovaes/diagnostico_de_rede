"""Parser pa    def __init__(self):
        # Padrão para linha de hop do MTR
        # HOST: hostname                    Loss%   Snt   Last   Avg  Best  Wrst StDev
        # Exemplo: "  2. AS???    152-255-239-67.user.vivozap.com.br (152.255.239.67)     0.0%    30    3.0   3.1   2.5  10.6   1.5"
        self.hop_pattern = re.compile(
            r'^\s*(\d+)\.\s+AS[\d?]*\s*(.+?)\s+([\d.]+)%\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
        )
        self.ip_pattern = re.compile(r'\(([\d.]+)\)')  # IP entre parêntesesados de MTR."""

import re
from typing import List, Optional
from datetime import datetime

from ..models.network_test import MTRResult, MTRHop, TestStatus


class MTRParser:
    """Parser para resultados do comando MTR."""
    
    def __init__(self):
        # Padrão para linha de hop do MTR
        # HOST: hostname                    Loss%   Snt   Last   Avg  Best  Wrst StDev
        # Exemplo: "  1. AS???    _gateway (10.15.10.1)                                   0.0%    10    0.2   0.2   0.1   0.3   0.0"
        self.hop_pattern = re.compile(
            r'^\s*(\d+)\.\s+AS\d*\s+(.+?)\s+([\d.]+)%\s+(\d+)\s+'
            r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
        )
        self.ip_pattern = re.compile(r'\(([\d.]+)\)')  # IP entre parênteses
    
    def parse(self, output: str, target: str) -> MTRResult:
        """Faz o parse da saída do comando MTR."""
        try:
            lines = output.strip().split('\n')
            hops = []
            
            for line in lines:
                hop = self._parse_hop_line(line)
                if hop:
                    hops.append(hop)
            
            # Calcula estatísticas agregadas de forma mais precisa
            if hops:
                # Perda total: maior perda encontrada entre os hops (worst case)
                total_loss = max(hop.loss_percent for hop in hops)
                
                # Latência: média apenas dos hops que responderam
                responding_hops = [hop for hop in hops if hop.avg_time > 0]
                avg_latency = sum(hop.avg_time for hop in responding_hops) / len(responding_hops) if responding_hops else 0
                
                # Se há hops com perda significativa, considera isso
                problematic_hops = [hop for hop in hops if hop.loss_percent > 5]
                if problematic_hops:
                    # Usa a média de perda dos hops problemáticos se for mais alta
                    problematic_loss = sum(hop.loss_percent for hop in problematic_hops) / len(problematic_hops)
                    total_loss = max(total_loss, problematic_loss)
            else:
                total_loss = 0
                avg_latency = 0
            
            # Determina status baseado em análise mais rigorosa
            status = TestStatus.SUCCESS
            if not hops:
                status = TestStatus.FAILED
            elif total_loss > 20:  # Perda crítica
                status = TestStatus.FAILED
            elif total_loss > 5 or avg_latency > 200:  # Problemas significativos
                status = TestStatus.WARNING
            elif any(hop.loss_percent > 10 for hop in hops):  # Hop específico com problema
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
                
                # Extrai o hostname completo do campo capturado
                hostname_raw = hostname.strip()
                
                # Se contém "???" significa que é AS desconhecido, mas pode ter hostname válido
                if "???" in hostname_raw:
                    # Procura por hostname válido após o ???
                    parts = hostname_raw.split()
                    hostname_final = None
                    ip_address = None
                    
                    for i, part in enumerate(parts):
                        if part != "???" and ("." in part or "(" in part):
                            # Encontrou início do hostname real
                            hostname_parts = parts[i:]
                            hostname_with_ip = " ".join(hostname_parts)
                            
                            # Extrai IP se estiver entre parênteses
                            ip_match = self.ip_pattern.search(hostname_with_ip)
                            if ip_match:
                                ip_address = ip_match.group(1)
                                hostname_final = hostname_with_ip.replace(f"({ip_address})", "").strip()
                            else:
                                hostname_final = hostname_with_ip
                                ip_address = hostname_with_ip
                            break
                    
                    # Se não encontrou hostname válido, usa placeholder
                    if not hostname_final:
                        hostname_final = "AS???"
                        ip_address = "AS???"
                else:
                    # Hostname sem AS prefix
                    ip_match = self.ip_pattern.search(hostname_raw)
                    if ip_match:
                        ip_address = ip_match.group(1)
                        hostname_final = hostname_raw.replace(f"({ip_address})", "").strip()
                    else:
                        hostname_final = hostname_raw
                        ip_address = hostname_raw
                
                return MTRHop(
                    hop_number=hop_number,
                    hostname=hostname_final,
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
