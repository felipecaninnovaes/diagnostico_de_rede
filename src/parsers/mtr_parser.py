"""Parser para resultados de MTR."""

import re
from typing import Optional
from datetime import datetime

from ..models.network_test import MTRResult, MTRHop, TestStatus


class MTRParser:
    """Parser para resultados do comando MTR."""

    def __init__(self):
        # Ex.: "  2. AS???    152-255-239-67.user.vivozap.com.br (152.255.239.67)     0.0%    30    3.0   3.1   2.5  10.6   1.5"
        # Ex.: "  6. AS15169  72.14.220.222                                           0.0%    30   17.3  17.5  17.0  24.5   1.3"
        self.hop_pattern = re.compile(
            r"^\s*(\d+)\.\s+AS\S+\s+(.+?)\s+"  # hop e campo hostname/ip (sem o AS)
            r"([\d.]+)%\s+(\d+)\s+"              # perda e enviados
            r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$"  # last/avg/best/wrst/stdev
        )
        self.ip_in_parens = re.compile(r"\(([\d.]+)\)")
        self.is_ipv4 = re.compile(r"^\d+\.\d+\.\d+\.\d+$")

    def parse(self, output: str, target: str) -> MTRResult:
        try:
            lines = output.strip().split("\n")
            hops = []
            for line in lines:
                hop = self._parse_hop_line(line)
                if hop:
                    hops.append(hop)

            if hops:
                total_loss = max(h.loss_percent for h in hops)
                responding = [h for h in hops if h.avg_time > 0]
                avg_latency = sum(h.avg_time for h in responding) / len(responding) if responding else 0.0
            else:
                total_loss = 0.0
                avg_latency = 0.0

            status = TestStatus.SUCCESS
            if not hops or total_loss > 20:
                status = TestStatus.FAILED if not hops or total_loss > 20 else TestStatus.SUCCESS
            elif total_loss > 5 or avg_latency > 200 or any(h.loss_percent > 10 for h in hops):
                status = TestStatus.WARNING

            return MTRResult(
                status=status,
                target=target,
                hops=hops,
                total_hops=len(hops),
                total_loss_percent=total_loss,
                avg_latency=avg_latency,
                timestamp=datetime.now(),
                raw_output=output,
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
                error_message=str(e),
            )

    def _parse_hop_line(self, line: str) -> Optional[MTRHop]:
        line_stripped = line.rstrip()
        if (not line_stripped or line_stripped.startswith("Start") or "HOST:" in line_stripped or "Loss%" in line_stripped):
            return None

        m = self.hop_pattern.match(line_stripped)
        if not m:
            return None

        hop_number = int(m.group(1))
        name_field = m.group(2).strip()
        loss_percent = float(m.group(3))
        sent_packets = int(m.group(4))
        last_time = float(m.group(5))
        avg_time = float(m.group(6))
        best_time = float(m.group(7))
        worst_time = float(m.group(8))
        std_dev = float(m.group(9))

        # Extrai IP entre parênteses, se houver
        ip_match = self.ip_in_parens.search(name_field)
        if ip_match:
            ip_address = ip_match.group(1)
            hostname = name_field.replace(f"({ip_address})", "").strip()
        else:
            # Sem parênteses: pode ser hostname puro, IP puro ou ???
            if self.is_ipv4.match(name_field):
                ip_address = name_field
                hostname = name_field  # sem reverse DNS
            else:
                hostname = name_field
                ip_address = name_field if self.is_ipv4.match(name_field) else (None if name_field == "???" else None)

        # Normaliza quando desconhecido
        if not hostname or hostname.upper().startswith("AS???") or hostname == "???":
            hostname = None
        if not ip_address:
            ip_address = hostname or "???"

        return MTRHop(
            hop_number=hop_number,
            hostname=hostname or "AS???",
            ip_address=ip_address,
            loss_percent=loss_percent,
            sent_packets=sent_packets,
            last_time=last_time,
            avg_time=avg_time,
            best_time=best_time,
            worst_time=worst_time,
            std_dev=std_dev,
        )
