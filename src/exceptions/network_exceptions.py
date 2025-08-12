"""Exceções customizadas para diagnóstico de rede."""


class NetworkDiagnosticException(Exception):
    """Exceção base para todas as exceções do diagnóstico de rede."""
    
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


class NetworkTestException(NetworkDiagnosticException):
    """Exceção base para erros em testes de rede."""
    pass


class DNSResolutionError(NetworkTestException):
    """Erro na resolução DNS."""
    
    def __init__(self, hostname: str, original_exception: Exception = None):
        self.hostname = hostname
        message = f"Falha na resolução DNS para '{hostname}'"
        super().__init__(message, original_exception)


class PingTestError(NetworkTestException):
    """Erro no teste de ping."""
    
    def __init__(self, target: str, reason: str, original_exception: Exception = None):
        self.target = target
        self.reason = reason
        message = f"Falha no teste de ping para '{target}': {reason}"
        super().__init__(message, original_exception)


class TracerouteTestError(NetworkTestException):
    """Erro no teste de traceroute."""
    
    def __init__(self, target: str, reason: str, original_exception: Exception = None):
        self.target = target
        self.reason = reason
        message = f"Falha no teste de traceroute para '{target}': {reason}"
        super().__init__(message, original_exception)


class MTRTestError(NetworkTestException):
    """Erro no teste MTR."""
    
    def __init__(self, target: str, reason: str, original_exception: Exception = None):
        self.target = target
        self.reason = reason
        message = f"Falha no teste MTR para '{target}': {reason}"
        super().__init__(message, original_exception)


class SpeedTestError(NetworkTestException):
    """Erro no teste de velocidade."""
    
    def __init__(self, reason: str, original_exception: Exception = None):
        self.reason = reason
        message = f"Falha no teste de velocidade: {reason}"
        super().__init__(message, original_exception)


class ISPDetectionError(NetworkDiagnosticException):
    """Erro na detecção do ISP."""
    
    def __init__(self, reason: str, original_exception: Exception = None):
        self.reason = reason
        message = f"Falha na detecção do ISP: {reason}"
        super().__init__(message, original_exception)


class ConfigurationError(NetworkDiagnosticException):
    """Erro de configuração."""
    
    def __init__(self, setting: str, reason: str, original_exception: Exception = None):
        self.setting = setting
        self.reason = reason
        message = f"Erro de configuração '{setting}': {reason}"
        super().__init__(message, original_exception)


class ReportGenerationError(NetworkDiagnosticException):
    """Erro na geração de relatórios."""
    
    def __init__(self, report_type: str, reason: str, original_exception: Exception = None):
        self.report_type = report_type
        self.reason = reason
        message = f"Falha na geração do relatório '{report_type}': {reason}"
        super().__init__(message, original_exception)
