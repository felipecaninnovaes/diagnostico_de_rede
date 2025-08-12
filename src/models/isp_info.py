"""Modelos para informações de ISP."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class IPType(Enum):
    """Tipos de IP."""
    PRIVATE = "private"
    PUBLIC = "public"
    UNKNOWN = "unknown"


class ISPProvider(Enum):
    """Provedores de internet suportados."""
    VIVO = "Vivo/Telefônica"
    NETFLEX = "Netflex (NET Claro)"
    OI = "Oi"
    TIM = "TIM"
    CLARO = "CLARO"
    UNKNOWN = "Desconhecido"


@dataclass
class ISPInfo:
    """Informações sobre o ISP detectado."""
    provider: ISPProvider
    public_ip: str
    hostname: Optional[str] = None
    confidence_level: float = 0.0
    
    @property
    def is_reliable(self) -> bool:
        """Indica se a detecção é confiável."""
        return self.confidence_level >= 0.6
