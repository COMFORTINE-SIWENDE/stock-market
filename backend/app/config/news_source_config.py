"""News source configuration parser for Kenyan news sources."""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


logger = logging.getLogger(__name__)


@dataclass
class NewsSource:
    """Represents a single news source."""
    
    name: str
    type: str  # 'rss' or 'api'
    url: str
    enabled: bool
    description: Optional[str] = None
    api_key_env: Optional[str] = None


@dataclass
class NewsSourceConfig:
    """Configuration for all news sources."""
    
    sources: List[NewsSource]
    
    @classmethod
    def load(cls, config_path: Path) -> "NewsSourceConfig":
        """
        Load news source configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        
        Returns:
            NewsSourceConfig object
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"News source config not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'sources' not in data:
                raise ValueError("Config must contain 'sources' key")
            
            sources = []
            for source_data in data['sources']:
                # Validate required fields
                required_fields = ['name', 'type', 'url', 'enabled']
                missing_fields = [f for f in required_fields if f not in source_data]
                if missing_fields:
                    logger.warning(
                        f"Skipping source due to missing fields: {missing_fields}. "
                        f"Source data: {source_data.get('name', 'unknown')}"
                    )
                    continue
                
                # Validate type
                if source_data['type'] not in ['rss', 'api']:
                    logger.warning(
                        f"Skipping source {source_data['name']}: "
                        f"invalid type '{source_data['type']}' (must be 'rss' or 'api')"
                    )
                    continue
                
                sources.append(NewsSource(
                    name=source_data['name'],
                    type=source_data['type'],
                    url=source_data['url'],
                    enabled=source_data['enabled'],
                    description=source_data.get('description'),
                    api_key_env=source_data.get('api_key_env')
                ))
            
            config = cls(sources=sources)
            config.validate()
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            raise ValueError(f"Invalid YAML in news source config: {e}")
        except Exception as e:
            logger.error(f"Failed to load news source config: {e}")
            raise
    
    def validate(self) -> None:
        """
        Validate the configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.sources:
            logger.warning("No news sources configured")
            return
        
        # Check for duplicate names
        names = [s.name for s in self.sources]
        duplicates = [name for name in names if names.count(name) > 1]
        if duplicates:
            raise ValueError(f"Duplicate source names found: {set(duplicates)}")
        
        # Check for duplicate URLs
        urls = [s.url for s in self.sources]
        duplicate_urls = [url for url in urls if urls.count(url) > 1]
        if duplicate_urls:
            logger.warning(f"Duplicate source URLs found: {set(duplicate_urls)}")
        
        # Log enabled sources
        enabled_sources = [s.name for s in self.sources if s.enabled]
        logger.info(f"Loaded {len(enabled_sources)} enabled news sources: {', '.join(enabled_sources)}")
    
    def get_enabled_sources(self) -> List[NewsSource]:
        """
        Get all enabled news sources.
        
        Returns:
            List of enabled NewsSource objects
        """
        return [s for s in self.sources if s.enabled]
    
    def get_rss_sources(self) -> List[NewsSource]:
        """
        Get all enabled RSS news sources.
        
        Returns:
            List of enabled RSS NewsSource objects
        """
        return [s for s in self.sources if s.enabled and s.type == 'rss']
    
    def get_api_sources(self) -> List[NewsSource]:
        """
        Get all enabled API news sources.
        
        Returns:
            List of enabled API NewsSource objects
        """
        return [s for s in self.sources if s.enabled and s.type == 'api']
    
    def to_yaml(self) -> str:
        """
        Serialize configuration to YAML format.
        
        Returns:
            YAML string representation
        """
        data = {
            'sources': [
                {
                    'name': s.name,
                    'type': s.type,
                    'url': s.url,
                    'enabled': s.enabled,
                    'description': s.description,
                    **(({'api_key_env': s.api_key_env} if s.api_key_env else {}))
                }
                for s in self.sources
            ]
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
