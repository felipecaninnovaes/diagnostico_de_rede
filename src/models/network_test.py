"""Modelos para testes de rede."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Status dos testes de rede."""
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class NetworkTest:
    """Teste de rede completo para um target."""
    target: str
    timestamp: datetime
    ping_result: Optional['PingResult'] = None
    traceroute_result: Optional['TracerouteResult'] = None
    mtr_result: Optional['MTRResult'] = None
    speed_test_result: Optional['SpeedTestResult'] = None


@dataclass
class PingResult:
    """Resultado de teste de ping."""
    status: TestStatus
    target: str
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_time: float
    avg_time: float
    max_time: float
    mdev_time: float
    timestamp: datetime
    raw_output: str
    error_message: Optional[str] = None


@dataclass
class TracerouteHop:
    """Salto individual do traceroute."""
    hop_number: int
    ip_address: str
    response_time: float
    is_timeout: bool = False


@dataclass
class TracerouteResult:
    """Resultado de teste de traceroute."""
    status: TestStatus
    target: str
    hops: List[TracerouteHop]
    total_hops: int
    timestamp: datetime
    raw_output: str
    error_message: Optional[str] = None


@dataclass
class MTRHop:
    """Salto individual do MTR."""
    hop_number: int
    hostname: str
    ip_address: str
    loss_percent: float
    sent_packets: int
    last_time: float
    avg_time: float
    best_time: float
    worst_time: float
    std_dev: float
    asn: Optional[str] = None


@dataclass
class MTRResult:
    """Resultado de teste MTR."""
    status: TestStatus
    target: str
    hops: List[MTRHop]
    total_hops: int
    total_loss_percent: float
    avg_latency: float
    timestamp: datetime
    raw_output: str
    error_message: Optional[str] = None


@dataclass
class SpeedTestResult:
    """Resultado de teste de velocidade."""
    status: TestStatus
    download_speed: float  # Mbps
    upload_speed: float    # Mbps
    ping_latency: float    # ms
    server_name: str
    server_location: str
    timestamp: datetime
    raw_output: str
    error_message: Optional[str] = None
