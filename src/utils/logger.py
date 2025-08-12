"""Utilitários para logging."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter que adiciona cores aos logs."""
    
    # Códigos de cor ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Aplica cor ao nome do nível
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(
    name: str = "network_diagnostic",
    level: str = "INFO",
    log_to_file: bool = True,
    log_file_path: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Se deve logar para arquivo
        log_file_path: Caminho do arquivo de log (opcional)
        use_colors: Se deve usar cores no console
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Remove handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Define nível
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Formato base
    base_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if use_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(base_format, date_format)
    else:
        console_formatter = logging.Formatter(base_format, date_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se solicitado)
    if log_to_file:
        if not log_file_path:
            # Cria diretório de logs
            log_dir = Path("./logs")
            log_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file_path = log_dir / f"network_diagnostic_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Formato mais detalhado para arquivo
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        file_formatter = logging.Formatter(file_format, date_format)
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def log_test_start(logger: logging.Logger, test_type: str, target: str):
    """Loga início de teste."""
    logger.info(f"Iniciando teste {test_type} para {target}")


def log_test_success(logger: logging.Logger, test_type: str, target: str, duration: float):
    """Loga sucesso de teste."""
    logger.info(f"Teste {test_type} para {target} concluído com sucesso em {duration:.2f}s")


def log_test_failure(logger: logging.Logger, test_type: str, target: str, error: str):
    """Loga falha de teste."""
    logger.error(f"Teste {test_type} para {target} falhou: {error}")


def log_test_warning(logger: logging.Logger, test_type: str, target: str, warning: str):
    """Loga aviso de teste."""
    logger.warning(f"Teste {test_type} para {target} com aviso: {warning}")


def log_isp_detection(logger: logging.Logger, provider: str, ip: str, confidence: float):
    """Loga detecção de ISP."""
    logger.info(f"ISP detectado: {provider} (IP: {ip}, Confiança: {confidence:.1%})")


def log_config_loaded(logger: logging.Logger, config_path: str):
    """Loga carregamento de configuração."""
    logger.info(f"Configuração carregada de: {config_path}")


def log_report_generated(logger: logging.Logger, report_type: str, file_path: str):
    """Loga geração de relatório."""
    logger.info(f"Relatório {report_type} gerado: {file_path}")


class LogContext:
    """Context manager para logging de operações."""
    
    def __init__(self, logger: logging.Logger, operation: str, target: str = ""):
        self.logger = logger
        self.operation = operation
        self.target = target
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        target_str = f" para {self.target}" if self.target else ""
        self.logger.info(f"Iniciando {self.operation}{target_str}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        target_str = f" para {self.target}" if self.target else ""
        
        if exc_type is None:
            self.logger.info(f"{self.operation}{target_str} concluído em {duration:.2f}s")
        else:
            self.logger.error(f"{self.operation}{target_str} falhou após {duration:.2f}s: {exc_val}")
        
        return False  # Não suprime exceções


# Logger padrão da aplicação
default_logger = setup_logger()
