"""Serviço para detecção de ISP."""

import re
import socket
import subprocess
from typing import Optional, Tuple, List
from dataclasses import dataclass

from ..models.isp_info import ISPInfo, ISPProvider, IPType
from ..exceptions import ISPDetectionError, NetworkTestException


@dataclass
class ISPDetectionRule:
    """Regra para detecção de ISP."""
    provider: ISPProvider
    ip_patterns: List[str]
    hostname_patterns: List[str]
    priority: int = 0


class ISPDetector:
    """Detector de provedores de internet."""
    
    def __init__(self):
        self._detection_rules = self._load_detection_rules()
    
    def _load_detection_rules(self) -> List[ISPDetectionRule]:
        """Carrega as regras de detecção de ISP."""
        return [
            # Vivo/Telefônica
            ISPDetectionRule(
                provider=ISPProvider.VIVO,
                ip_patterns=[
                    r"^200\.142\.",
                    r"^191\.36\.",
                    r"^200\.225\.",
                    r"^187\.72\.",
                    r"^200\.171\.",
                    r"^177\.37\.",
                    r"^179\.191\.",
                    r"^201\.17\.",
                ],
                hostname_patterns=[
                    r".*telefonica.*",
                    r".*vivo.*",
                    r".*speedy.*",
                    r".*telesp.*",
                ],
                priority=10
            ),
            
            # Netflex (NET Claro)
            ISPDetectionRule(
                provider=ISPProvider.NETFLEX,
                ip_patterns=[
                    r"^201\.23\.",
                    r"^201\.6\.",
                    r"^179\.184\.",
                    r"^201\.22\.",
                    r"^170\.79\.",
                    r"^170\.244\.",
                    r"^45\.5\.",
                ],
                hostname_patterns=[
                    r".*net.*",
                    r".*claro.*",
                    r".*netflex.*",
                    r".*embratel.*",
                ],
                priority=10
            ),
            
            # Oi
            ISPDetectionRule(
                provider=ISPProvider.OI,
                ip_patterns=[
                    r"^200\.147\.",
                    r"^200\.144\.",
                    r"^179\.191\.",
                    r"^201\.35\.",
                ],
                hostname_patterns=[
                    r".*oi\.com\.br.*",
                    r".*telemar.*",
                    r".*velox.*",
                ],
                priority=8
            ),
            
            # TIM
            ISPDetectionRule(
                provider=ISPProvider.TIM,
                ip_patterns=[
                    r"^187\.4\.",
                    r"^200\.155\.",
                    r"^179\.184\.",
                ],
                hostname_patterns=[
                    r".*tim\.com\.br.*",
                    r".*intelig.*",
                ],
                priority=8
            ),
            ISPDetectionRule(
                provider=ISPProvider.CLARO,
                ip_patterns=[
                    r"^187\.39\.",
                ],
                hostname_patterns=[
                    r".*virtua\.com\.br.*",
                ],
                priority=8
            ),
        ]
    
    def detect_public_ip(self) -> Tuple[str, IPType]:
        """Detecta o IP público atual."""
        services = [
            ("https://httpbin.org/ip", "json", "origin"),
            ("https://api.ipify.org", "text", None),
            ("https://ipinfo.io/ip", "text", None),
        ]
        
        for url, response_type, field in services:
            try:
                import requests
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                if response_type == "json":
                    ip = response.json().get(field)
                else:
                    ip = response.text.strip()
                
                if self._is_valid_ip(ip):
                    ip_type = self._classify_ip(ip)
                    return ip, ip_type
                    
            except Exception as e:
                continue
        
        raise ISPDetectionError("Não foi possível detectar o IP público")
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Verifica se o IP é válido."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    def _classify_ip(self, ip: str) -> IPType:
        """Classifica o tipo de IP."""
        octets = ip.split('.')
        first_octet = int(octets[0])
        second_octet = int(octets[1])
        
        # IP privado
        if (first_octet == 10 or
            (first_octet == 172 and 16 <= second_octet <= 31) or
            (first_octet == 192 and second_octet == 168)):
            return IPType.PRIVATE
        
        # IP público
        return IPType.PUBLIC
    
    def detect_isp_from_ip(self, ip: str) -> Optional[ISPInfo]:
        """Detecta o ISP baseado no IP."""
        best_match = None
        best_score = 0
        
        for rule in self._detection_rules:
            score = 0
            
            # Verifica padrões de IP
            for pattern in rule.ip_patterns:
                if re.match(pattern, ip):
                    score += rule.priority * 2
                    break
            
            if score > best_score:
                best_score = score
                best_match = rule.provider
        
        if best_match:
            return ISPInfo(
                provider=best_match,
                public_ip=ip,
                hostname=self._get_hostname_for_ip(ip),
                confidence_level=min(best_score / 10.0, 1.0)
            )
        
        return None
    
    def detect_isp_from_hostname(self, hostname: str) -> Optional[ISPInfo]:
        """Detecta o ISP baseado no hostname."""
        best_match = None
        best_score = 0
        
        for rule in self._detection_rules:
            score = 0
            
            # Verifica padrões de hostname
            for pattern in rule.hostname_patterns:
                if re.search(pattern, hostname.lower()):
                    score += rule.priority
                    break
            
            if score > best_score:
                best_score = score
                best_match = rule.provider
        
        if best_match:
            return ISPInfo(
                provider=best_match,
                public_ip="",
                hostname=hostname,
                confidence_level=min(best_score / 10.0, 1.0)
            )
        
        return None
    
    def _get_hostname_for_ip(self, ip: str) -> str:
        """Obtém o hostname para um IP."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except (socket.herror, socket.gaierror):
            return ""
    
    def detect_isp_comprehensive(self) -> ISPInfo:
        """Detecta o ISP usando múltiplas abordagens."""
        try:
            # Detecta IP público
            public_ip, ip_type = self.detect_public_ip()
            
            # Tenta detectar por IP
            isp_info = self.detect_isp_from_ip(public_ip)
            
            # Se não conseguiu detectar por IP, tenta por hostname
            if not isp_info:
                hostname = self._get_hostname_for_ip(public_ip)
                if hostname:
                    isp_info = self.detect_isp_from_hostname(hostname)
            
            # Se ainda não conseguiu, retorna informação básica
            if not isp_info:
                isp_info = ISPInfo(
                    provider=ISPProvider.UNKNOWN,
                    public_ip=public_ip,
                    hostname=self._get_hostname_for_ip(public_ip),
                    confidence_level=0.0
                )
            else:
                # Atualiza com IP público detectado
                isp_info.public_ip = public_ip
                if not isp_info.hostname:
                    isp_info.hostname = self._get_hostname_for_ip(public_ip)
            
            return isp_info
            
        except Exception as e:
            raise ISPDetectionError(f"Falha na detecção comprehensiva do ISP: {str(e)}", e)
