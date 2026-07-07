import time
from pathlib import Path
from typing import List
from dataclasses import dataclass, field

@dataclass
class WorkMetadata:
    """Metadata for an ASMR work."""
    rj_id: str
    title: str
    circle: str
    cv: List[str]
    tags: List[str]
    price: int
    dl_count: int
    source_url: str
    rating: float
    release_date: str
    cover_url: str
    total_size: int = 0

@dataclass
class TrackItem:
    """Represents a track or folder in the download hierarchy."""
    id: str
    title: str
    type: str
    url: str
    size: int
    save_path: Path
    level: int = 0
    children: List['TrackItem'] = field(default_factory=list)

@dataclass
class SessionStats:
    """Statistics for a download session."""
    success: int = 0
    failed: int = 0
    skipped: int = 0
    bytes_downloaded: int = 0
    start_time: float = field(default_factory=time.time)
    failures: list = field(default_factory=list)  # list of (filename, reason) tuples
