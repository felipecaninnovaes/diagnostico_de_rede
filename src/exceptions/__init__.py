"""Exceções customizadas para o diagnóstico de rede."""

from .network_exceptions import (
    NetworkDiagnosticException,
    NetworkTestException,
    DNSResolutionError,
    PingTestError,
    TracerouteTestError,
    MTRTestError,
    SpeedTestError,
    ISPDetectionError,
    ConfigurationError,
    ReportGenerationError
)

__all__ = [
    'NetworkDiagnosticException',
    'NetworkTestException', 
    'DNSResolutionError',
    'PingTestError',
    'TracerouteTestError',
    'MTRTestError',
    'SpeedTestError',
    'ISPDetectionError',
    'ConfigurationError',
    'ReportGenerationError'
]
