"""
Utilities for loading and managing individual source configurations.

Each source has its own YAML file in configs/sources/ that defines
how to scrape/search that source, including selectors, API endpoints,
rate limits, and tool preferences.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import load_yaml


def load_source_config(source_id: str, configs_dir: str = "configs/sources") -> Optional[Dict[str, Any]]:
    """
    Load configuration for a specific source from its YAML file.
    
    Args:
        source_id: The source identifier (e.g., "ownerama", "zillow")
        configs_dir: Directory containing source config files
        
    Returns:
        Source configuration dict, or None if not found
    """
    config_path = Path(configs_dir) / f"{source_id}.yaml"
    
    if not config_path.exists():
        return None
    
    return load_yaml(str(config_path))


def load_all_source_configs(configs_dir: str = "configs/sources") -> Dict[str, Dict[str, Any]]:
    """
    Load all source configurations from the configs/sources/ directory.
    
    Args:
        configs_dir: Directory containing source config files
        
    Returns:
        Dict mapping source_id to configuration dict
    """
    configs = {}
    configs_path = Path(configs_dir)
    
    if not configs_path.exists():
        return configs
    
    # Load all YAML files except template and README
    for config_file in configs_path.glob("*.yaml"):
        if config_file.name.startswith(".") or config_file.name == "README.md":
            continue
        
        source_id = config_file.stem
        try:
            config = load_yaml(str(config_file))
            if config and "source_id" in config:
                # Use source_id from config if it differs from filename
                actual_id = config["source_id"]
                configs[actual_id] = config
            else:
                configs[source_id] = config
        except Exception:
            # Skip invalid config files
            continue
    
    return configs


def get_enabled_sources(configs_dir: str = "configs/sources") -> List[str]:
    """
    Get list of source IDs that are enabled.
    
    Args:
        configs_dir: Directory containing source config files
        
    Returns:
        List of enabled source IDs
    """
    all_configs = load_all_source_configs(configs_dir)
    return [
        source_id
        for source_id, config in all_configs.items()
        if config.get("enabled", False)
    ]


def get_source_method(source_id: str, configs_dir: str = "configs/sources") -> Optional[str]:
    """
    Get the scraping/search method for a source.
    
    Returns one of: "api", "playwright", "requests", "rss", "selenium", "contact_required"
    """
    config = load_source_config(source_id, configs_dir)
    if not config:
        return None
    return config.get("method")


def get_source_rate_limit(source_id: str, configs_dir: str = "configs/sources") -> int:
    """
    Get the rate limit (seconds between requests) for a source.
    
    Returns default of 30 seconds if not specified.
    """
    config = load_source_config(source_id, configs_dir)
    if not config:
        return 30
    return config.get("rate_limit_seconds", 30)
