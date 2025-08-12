"""Serviço principal para execução de testes de rede."""

import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.network_test import (
    NetworkTest, PingResult, TracerouteResult, MTRResult, 
    SpeedTestResult, TestStatus
)
from ..models.test_results import TestResults, TestSummary
from ..models.isp_info import ISPInfo
from ..exceptions import (
    NetworkTestException, PingTestError, TracerouteTestError,
    MTRTestError, SpeedTestError
)
from .isp_detector import ISPDetector
from ..parsers.ping_parser import PingParser
from ..parsers.traceroute_parser import TracerouteParser
from ..parsers.mtr_parser import MTRParser


class NetworkTestService:
    """Serviço principal para execução de testes de rede."""
    
    def __init__(self):
        self.isp_detector = ISPDetector()
        self.ping_parser = PingParser()
        self.traceroute_parser = TracerouteParser()
        self.mtr_parser = MTRParser()
        self._current_tests: Dict[str, NetworkTest] = {}
    
    async def run_comprehensive_test(self, targets: List[str]) -> TestResults:
        """Executa teste comprehensivo de rede."""
        # Detecta ISP
        isp_info = self.isp_detector.detect_isp_comprehensive()
        
        # Executa testes
        test_results = TestResults(
            timestamp=datetime.now(),
            isp_info=isp_info,
            tests=[]
        )
        
        # Executa testes para cada target
        for target in targets:
            network_test = await self._run_single_target_test(target)
            test_results.tests.append(network_test)
        
        return test_results
    
    async def _run_single_target_test(self, target: str) -> NetworkTest:
        """Executa teste completo para um target específico."""
        test = NetworkTest(
            target=target,
            timestamp=datetime.now(),
            ping_result=None,
            traceroute_result=None,
            mtr_result=None,
            speed_test_result=None
        )
        
        self._current_tests[target] = test
        
        try:
            # Executa testes em paralelo quando possível
            ping_task = self._run_ping_test(target)
            traceroute_task = self._run_traceroute_test(target)
            mtr_task = self._run_mtr_test(target)
            
            # Aguarda testes básicos
            ping_result, traceroute_result, mtr_result = await asyncio.gather(
                ping_task, traceroute_task, mtr_task,
                return_exceptions=True
            )
            
            # Processa resultados
            if isinstance(ping_result, PingResult):
                test.ping_result = ping_result
            
            if isinstance(traceroute_result, TracerouteResult):
                test.traceroute_result = traceroute_result
            
            if isinstance(mtr_result, MTRResult):
                test.mtr_result = mtr_result
            
            # Executa teste de velocidade se necessário
            if target in ["8.8.8.8", "1.1.1.1"]:  # Apenas para targets específicos
                try:
                    speed_result = await self._run_speed_test()
                    test.speed_test_result = speed_result
                except Exception:
                    pass  # Teste de velocidade é opcional
        
        except Exception as e:
            # Log error mas não falha o teste completo
            pass
        
        finally:
            if target in self._current_tests:
                del self._current_tests[target]
        
        return test
    
    async def _run_ping_test(self, target: str) -> PingResult:
        """Executa teste de ping."""
        try:
            # Executa comando ping
            cmd = f"ping -c 4 {target}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise PingTestError(
                    target=target,
                    reason=stderr.decode().strip() if stderr else "Ping falhou"
                )
            
            # Parse do resultado
            output = stdout.decode()
            return self.ping_parser.parse(output, target)
            
        except Exception as e:
            if isinstance(e, PingTestError):
                raise
            raise PingTestError(target=target, reason=str(e), original_exception=e)
    
    async def _run_traceroute_test(self, target: str) -> TracerouteResult:
        """Executa teste de traceroute."""
        try:
            # Executa comando traceroute
            cmd = f"traceroute -n {target}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise TracerouteTestError(
                    target=target,
                    reason=stderr.decode().strip() if stderr else "Traceroute falhou"
                )
            
            # Parse do resultado
            output = stdout.decode()
            return self.traceroute_parser.parse(output, target)
            
        except Exception as e:
            if isinstance(e, TracerouteTestError):
                raise
            raise TracerouteTestError(target=target, reason=str(e), original_exception=e)
    
    async def _run_mtr_test(self, target: str) -> MTRResult:
        """Executa teste MTR."""
        try:
            # Executa comando mtr
            cmd = f"mtr -r -c 10 {target}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise MTRTestError(
                    target=target,
                    reason=stderr.decode().strip() if stderr else "MTR falhou"
                )
            
            # Parse do resultado
            output = stdout.decode()
            return self.mtr_parser.parse(output, target)
            
        except Exception as e:
            if isinstance(e, MTRTestError):
                raise
            raise MTRTestError(target=target, reason=str(e), original_exception=e)
    
    async def _run_speed_test(self) -> SpeedTestResult:
        """Executa teste de velocidade."""
        try:
            # Executa speedtest-cli
            cmd = "speedtest-cli --json"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise SpeedTestError(
                    reason=stderr.decode().strip() if stderr else "Speedtest falhou"
                )
            
            # Parse do resultado JSON
            import json
            data = json.loads(stdout.decode())
            
            return SpeedTestResult(
                status=TestStatus.SUCCESS,
                download_speed=data.get('download', 0) / 1_000_000,  # Convert to Mbps
                upload_speed=data.get('upload', 0) / 1_000_000,      # Convert to Mbps
                ping_latency=data.get('ping', 0),
                server_name=data.get('server', {}).get('name', ''),
                server_location=data.get('server', {}).get('country', ''),
                timestamp=datetime.now(),
                raw_output=stdout.decode()
            )
            
        except Exception as e:
            if isinstance(e, SpeedTestError):
                raise
            raise SpeedTestError(reason=str(e), original_exception=e)
    
    def get_test_progress(self, target: str) -> Optional[Dict[str, Any]]:
        """Obtém o progresso do teste para um target específico."""
        if target not in self._current_tests:
            return None
        
        test = self._current_tests[target]
        
        completed_tests = 0
        total_tests = 4  # ping, traceroute, mtr, speed (opcional)
        
        if test.ping_result:
            completed_tests += 1
        if test.traceroute_result:
            completed_tests += 1
        if test.mtr_result:
            completed_tests += 1
        if test.speed_test_result:
            completed_tests += 1
        
        return {
            "target": target,
            "completed": completed_tests,
            "total": total_tests,
            "progress": completed_tests / total_tests,
            "status": "running"
        }
    
    def cancel_test(self, target: str) -> bool:
        """Cancela teste em execução para um target."""
        if target in self._current_tests:
            del self._current_tests[target]
            return True
        return False
    
    def cancel_all_tests(self) -> int:
        """Cancela todos os testes em execução."""
        count = len(self._current_tests)
        self._current_tests.clear()
        return count
