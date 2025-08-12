"""__init__.py para utils."""

from .validators import (
    is_valid_ip,
    is_valid_hostname,
    is_valid_url,
    validate_target,
    validate_targets,
    validate_port,
    validate_timeout,
    validate_count,
    normalize_hostname,
    extract_domain_from_email,
    get_ip_version,
    is_private_ip,
    format_bytes,
    format_duration,
)

from .logger import (
    setup_logger,
    ColoredFormatter,
    LogContext,
    log_test_start,
    log_test_success,
    log_test_failure,
    log_test_warning,
    log_isp_detection,
    log_config_loaded,
    log_report_generated,
    default_logger,
)

__all__ = [
    # Validators
    "is_valid_ip",
    "is_valid_hostname", 
    "is_valid_url",
    "validate_target",
    "validate_targets",
    "validate_port",
    "validate_timeout",
    "validate_count",
    "normalize_hostname",
    "extract_domain_from_email",
    "get_ip_version",
    "is_private_ip",
    "format_bytes",
    "format_duration",
    
    # Logger
    "setup_logger",
    "ColoredFormatter",
    "LogContext",
    "log_test_start",
    "log_test_success",
    "log_test_failure",
    "log_test_warning",
    "log_isp_detection",
    "log_config_loaded",
    "log_report_generated",
    "default_logger",
]
