"""Utilitários para validação de entrada."""

import re
import socket
from typing import List, Tuple, Optional
from urllib.parse import urlparse


def is_valid_ip(ip: str) -> bool:
    """Verifica se uma string é um IP válido (IPv4 ou IPv6)."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False


def is_valid_hostname(hostname: str) -> bool:
    """Verifica se uma string é um hostname válido."""
    if not hostname or len(hostname) > 253:
        return False
    
    # Remove ponto final se presente
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    
    # Verifica cada label
    allowed = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$")
    labels = hostname.split(".")
    
    if not labels:
        return False
    
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not allowed.match(label):
            return False
    
    return True


def is_valid_url(url: str) -> bool:
    """Verifica se uma string é uma URL válida."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_target(target: str) -> Tuple[bool, str, str]:
    """
    Valida um target de teste.
    
    Returns:
        Tuple[bool, str, str]: (é_válido, tipo_target, mensagem_erro)
    """
    if not target or not isinstance(target, str):
        return False, "unknown", "Target não pode ser vazio"
    
    target = target.strip()
    
    if is_valid_ip(target):
        return True, "ip", ""
    
    if is_valid_hostname(target):
        return True, "hostname", ""
    
    if is_valid_url(target):
        return True, "url", ""
    
    return False, "unknown", f"'{target}' não é um IP, hostname ou URL válido"


def validate_targets(targets: List[str]) -> Tuple[List[str], List[str]]:
    """
    Valida uma lista de targets.
    
    Returns:
        Tuple[List[str], List[str]]: (targets_válidos, erros)
    """
    valid_targets = []
    errors = []
    
    if not targets:
        errors.append("Lista de targets não pode ser vazia")
        return valid_targets, errors
    
    for i, target in enumerate(targets):
        is_valid, target_type, error_msg = validate_target(target)
        
        if is_valid:
            valid_targets.append(target.strip())
        else:
            errors.append(f"Target {i+1}: {error_msg}")
    
    return valid_targets, errors


def validate_port(port: str) -> Tuple[bool, Optional[int], str]:
    """
    Valida número de porta.
    
    Returns:
        Tuple[bool, Optional[int], str]: (é_válido, porta_int, mensagem_erro)
    """
    try:
        port_int = int(port)
        if 1 <= port_int <= 65535:
            return True, port_int, ""
        else:
            return False, None, "Porta deve estar entre 1 e 65535"
    except ValueError:
        return False, None, "Porta deve ser um número inteiro"


def validate_timeout(timeout: str) -> Tuple[bool, Optional[int], str]:
    """
    Valida valor de timeout.
    
    Returns:
        Tuple[bool, Optional[int], str]: (é_válido, timeout_int, mensagem_erro)
    """
    try:
        timeout_int = int(timeout)
        if timeout_int > 0:
            return True, timeout_int, ""
        else:
            return False, None, "Timeout deve ser maior que 0"
    except ValueError:
        return False, None, "Timeout deve ser um número inteiro"


def validate_count(count: str, min_value: int = 1, max_value: int = 100) -> Tuple[bool, Optional[int], str]:
    """
    Valida valor de contagem.
    
    Returns:
        Tuple[bool, Optional[int], str]: (é_válido, count_int, mensagem_erro)
    """
    try:
        count_int = int(count)
        if min_value <= count_int <= max_value:
            return True, count_int, ""
        else:
            return False, None, f"Contagem deve estar entre {min_value} e {max_value}"
    except ValueError:
        return False, None, "Contagem deve ser um número inteiro"


def normalize_hostname(hostname: str) -> str:
    """Normaliza hostname removendo esquemas e barras."""
    if not hostname:
        return hostname
    
    # Remove esquema se presente
    if "://" in hostname:
        hostname = hostname.split("://", 1)[1]
    
    # Remove path se presente
    if "/" in hostname:
        hostname = hostname.split("/")[0]
    
    # Remove porta se presente
    if ":" in hostname and not hostname.count(":") > 1:  # Não é IPv6
        hostname = hostname.split(":")[0]
    
    return hostname.strip().lower()


def extract_domain_from_email(email: str) -> Optional[str]:
    """Extrai domínio de um endereço de email."""
    if "@" not in email:
        return None
    
    domain = email.split("@")[-1].strip()
    return domain if is_valid_hostname(domain) else None


def get_ip_version(ip: str) -> Optional[str]:
    """Retorna versão do IP (4 ou 6)."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return "4"
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return "6"
        except socket.error:
            return None


def is_private_ip(ip: str) -> bool:
    """Verifica se o IP é privado."""
    if not is_valid_ip(ip):
        return False
    
    try:
        # Para IPv4
        octets = ip.split('.')
        if len(octets) == 4:
            first = int(octets[0])
            second = int(octets[1])
            
            # 10.0.0.0/8
            if first == 10:
                return True
            
            # 172.16.0.0/12
            if first == 172 and 16 <= second <= 31:
                return True
            
            # 192.168.0.0/16
            if first == 192 and second == 168:
                return True
            
            # 127.0.0.0/8 (loopback)
            if first == 127:
                return True
        
        # Para IPv6 - implementação básica
        if "::" in ip or ip.startswith("fe80:") or ip.startswith("fc00:") or ip.startswith("fd00:"):
            return True
            
    except ValueError:
        pass
    
    return False


def format_bytes(bytes_value: int) -> str:
    """Formata bytes em unidades legíveis."""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Formata duração em formato legível."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
