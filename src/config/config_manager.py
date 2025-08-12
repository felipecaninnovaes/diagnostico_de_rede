"""Gerenciador de configurações da aplicação."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..exceptions import ConfigurationError


@dataclass
class TestSettings:
    """Configurações de teste."""
    ping_count: int = 4
    ping_timeout: int = 10
    traceroute_max_hops: int = 30
    traceroute_timeout: int = 5
    mtr_count: int = 10
    mtr_timeout: int = 60
    speed_test_enabled: bool = True
    speed_test_timeout: int = 120


@dataclass
class ReportSettings:
    """Configurações de relatório."""
    output_directory: str = "./reports"
    formats: List[str] = None
    auto_open: bool = False
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ["json", "text", "csv"]


@dataclass
class UISettings:
    """Configurações de interface."""
    show_progress: bool = True
    show_detailed_output: bool = False
    console_width: int = 120
    color_theme: str = "auto"


@dataclass
class NetworkSettings:
    """Configurações de rede."""
    max_concurrent_tests: int = 3
    retry_attempts: int = 2
    connection_timeout: int = 10


@dataclass
class ISPDetectionSettings:
    """Configurações de detecção de ISP."""
    confidence_threshold: float = 0.5
    fallback_services: List[str] = None
    
    def __post_init__(self):
        if self.fallback_services is None:
            self.fallback_services = [
                "https://httpbin.org/ip",
                "https://api.ipify.org", 
                "https://ipinfo.io/ip"
            ]


class ConfigManager:
    """Gerenciador de configurações da aplicação."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self._config_data: Dict[str, Any] = {}
        self.load_config()
    
    def _get_default_config_path(self) -> Path:
        """Obtém o caminho padrão do arquivo de configuração."""
        # Procura por arquivo de configuração em várias localizações
        possible_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml", 
            Path(__file__).parent / "default_config.yaml",
            Path.home() / ".network_diagnostic" / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Retorna o caminho padrão se nenhum arquivo for encontrado
        return Path(__file__).parent / "default_config.yaml"
    
    def load_config(self):
        """Carrega configurações do arquivo YAML."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
            else:
                # Usa configurações padrão se arquivo não existir
                self._config_data = self._get_default_config()
                
        except yaml.YAMLError as e:
            raise ConfigurationError(
                setting="arquivo_config",
                reason=f"Erro ao parsear YAML: {str(e)}",
                original_exception=e
            )
        except Exception as e:
            raise ConfigurationError(
                setting="arquivo_config",
                reason=f"Erro ao carregar configuração: {str(e)}",
                original_exception=e
            )
    
    def save_config(self, config_path: Optional[str] = None):
        """Salva configurações no arquivo YAML."""
        try:
            target_path = Path(config_path) if config_path else self.config_path
            
            # Cria diretório se não existir
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            raise ConfigurationError(
                setting="salvar_config",
                reason=f"Erro ao salvar configuração: {str(e)}",
                original_exception=e
            )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão."""
        return {
            "default_targets": [
                "8.8.8.8",
                "1.1.1.1", 
                "208.67.222.222",
                "9.9.9.9"
            ],
            "test_settings": {
                "ping": {"count": 4, "timeout": 10},
                "traceroute": {"max_hops": 30, "timeout": 5},
                "mtr": {"count": 10, "timeout": 60},
                "speed_test": {"enabled": True, "timeout": 120}
            },
            "report_settings": {
                "output_directory": "./reports",
                "formats": ["json", "text", "csv"],
                "auto_open": False
            },
            "ui_settings": {
                "show_progress": True,
                "show_detailed_output": False,
                "console_width": 120,
                "color_theme": "auto"
            },
            "network_settings": {
                "max_concurrent_tests": 3,
                "retry_attempts": 2,
                "connection_timeout": 10
            },
            "isp_detection": {
                "confidence_threshold": 0.5,
                "fallback_services": [
                    "https://httpbin.org/ip",
                    "https://api.ipify.org",
                    "https://ipinfo.io/ip"
                ]
            }
        }
    
    def get_default_targets(self) -> List[str]:
        """Obtém lista de targets padrão."""
        return self._config_data.get("default_targets", ["8.8.8.8", "1.1.1.1"])
    
    def get_test_settings(self) -> TestSettings:
        """Obtém configurações de teste."""
        test_config = self._config_data.get("test_settings", {})
        
        return TestSettings(
            ping_count=test_config.get("ping", {}).get("count", 4),
            ping_timeout=test_config.get("ping", {}).get("timeout", 10),
            traceroute_max_hops=test_config.get("traceroute", {}).get("max_hops", 30),
            traceroute_timeout=test_config.get("traceroute", {}).get("timeout", 5),
            mtr_count=test_config.get("mtr", {}).get("count", 10),
            mtr_timeout=test_config.get("mtr", {}).get("timeout", 60),
            speed_test_enabled=test_config.get("speed_test", {}).get("enabled", True),
            speed_test_timeout=test_config.get("speed_test", {}).get("timeout", 120)
        )
    
    def get_report_settings(self) -> ReportSettings:
        """Obtém configurações de relatório."""
        report_config = self._config_data.get("report_settings", {})
        
        return ReportSettings(
            output_directory=report_config.get("output_directory", "./reports"),
            formats=report_config.get("formats", ["json", "text", "csv"]),
            auto_open=report_config.get("auto_open", False)
        )
    
    def get_ui_settings(self) -> UISettings:
        """Obtém configurações de interface."""
        ui_config = self._config_data.get("ui_settings", {})
        
        return UISettings(
            show_progress=ui_config.get("show_progress", True),
            show_detailed_output=ui_config.get("show_detailed_output", False),
            console_width=ui_config.get("console_width", 120),
            color_theme=ui_config.get("color_theme", "auto")
        )
    
    def get_network_settings(self) -> NetworkSettings:
        """Obtém configurações de rede."""
        network_config = self._config_data.get("network_settings", {})
        
        return NetworkSettings(
            max_concurrent_tests=network_config.get("max_concurrent_tests", 3),
            retry_attempts=network_config.get("retry_attempts", 2),
            connection_timeout=network_config.get("connection_timeout", 10)
        )
    
    def get_isp_detection_settings(self) -> ISPDetectionSettings:
        """Obtém configurações de detecção de ISP."""
        isp_config = self._config_data.get("isp_detection", {})
        
        return ISPDetectionSettings(
            confidence_threshold=isp_config.get("confidence_threshold", 0.5),
            fallback_services=isp_config.get("fallback_services", [
                "https://httpbin.org/ip",
                "https://api.ipify.org",
                "https://ipinfo.io/ip"
            ])
        )
    
    def update_setting(self, section: str, key: str, value: Any):
        """Atualiza uma configuração específica."""
        if section not in self._config_data:
            self._config_data[section] = {}
        
        self._config_data[section][key] = value
    
    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Obtém uma configuração específica."""
        return self._config_data.get(section, {}).get(key, default)
    
    def reset_to_defaults(self):
        """Reseta configurações para os valores padrão."""
        self._config_data = self._get_default_config()
    
    def validate_config(self) -> List[str]:
        """Valida configurações e retorna lista de erros."""
        errors = []
        
        # Valida targets
        targets = self.get_default_targets()
        if not targets:
            errors.append("Lista de targets padrão está vazia")
        
        # Valida configurações de teste
        test_settings = self.get_test_settings()
        if test_settings.ping_count <= 0:
            errors.append("Contagem de ping deve ser maior que 0")
        if test_settings.ping_timeout <= 0:
            errors.append("Timeout de ping deve ser maior que 0")
        
        # Valida configurações de rede
        network_settings = self.get_network_settings()
        if network_settings.max_concurrent_tests <= 0:
            errors.append("Número máximo de testes concorrentes deve ser maior que 0")
        
        return errors
