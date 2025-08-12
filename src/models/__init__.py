"""Modelos de dados para o diagnóstico de rede."""

from .network_test import NetworkTest, PingResult, TracerouteResult, MTRResult, SpeedTestResult
from .isp_info import ISPInfo, ISPProvider
from .test_results import TestResults, TestSummary

__all__ = [
    'NetworkTest',
    'PingResult', 
    'TracerouteResult',
    'MTRResult',
    'SpeedTestResult',
    'ISPInfo',
    'ISPProvider', 
    'TestResults',
    'TestSummary'
]
