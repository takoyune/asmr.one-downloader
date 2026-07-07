import json
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError

from main.constants import HOSTNAME_MIRRORS, CONFIG_FILE

class ConfigSchema(BaseModel):
    output_dir: str = Field(default="Downloads")
    max_concurrent: int = Field(default=3, gt=0, le=20)
    proxy: Optional[str] = Field(default=None)
    mirror: str = Field(default=HOSTNAME_MIRRORS[0])
    tag_audio: bool = Field(default=True)
    sort_files: bool = Field(default=False)
    dir_template: str = Field(default="RJ{rj_id} {title}")
    timeout: int = Field(default=60, gt=0)
    dns: str = Field(default="1.1.1.1")
    bandwidth_limit_mbps: float = Field(default=0.0, ge=0.0)
    format_priority: List[str] = Field(default_factory=lambda: ["flac", "wav", "mp3", "m4a", "ogg"])
    last_update_check: float = Field(default=0.0)

class ConfigManager:
    """Manages application configuration."""
    def __init__(self, data: ConfigSchema = None):
        if data is None:
            data = ConfigSchema()
        self.output_dir = Path(data.output_dir)
        self.max_concurrent = data.max_concurrent
        self.proxy = data.proxy
        self.mirror = data.mirror
        self.tag_audio = data.tag_audio
        self.sort_files = data.sort_files
        self.dir_template = data.dir_template
        self.timeout = data.timeout
        self.dns = data.dns
        self.bandwidth_limit_mbps = data.bandwidth_limit_mbps
        self.format_priority = data.format_priority
        self.last_update_check = data.last_update_check

    @classmethod
    def load(cls) -> 'ConfigManager':
        """Load configuration from file or create default."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                schema = ConfigSchema(**raw_data)
                instance = cls(schema)
                instance.save()
                return instance
                    
            except ValidationError as e:
                logging.error("Configuration validation failed!")
                for err in e.errors():
                    logging.error(f"  Field '{err['loc'][0]}': {err['msg']}")
                logging.warning("Falling back to default configuration due to invalid config.json.")
            except (json.JSONDecodeError, KeyError, ValueError, IOError) as e:
                logging.warning(f"Config load error: {e}, using defaults")
        
        instance = cls()
        instance.save()
        return instance

    def save(self) -> None:
        """Save configuration to file."""
        data = {
            "output_dir": str(self.output_dir),
            "max_concurrent": self.max_concurrent,
            "proxy": self.proxy,
            "mirror": self.mirror,
            "tag_audio": self.tag_audio,
            "sort_files": self.sort_files,
            "dir_template": self.dir_template,
            "timeout": self.timeout,
            "dns": self.dns,
            "bandwidth_limit_mbps": self.bandwidth_limit_mbps,
            "format_priority": self.format_priority,
            "last_update_check": self.last_update_check
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Failed to save config: {e}")
