import logging
import mimetypes
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3

from main.models import WorkMetadata

class AudioProcessor:
    """Handles audio file tagging with metadata."""
    @staticmethod
    def apply_tags(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Apply metadata tags to audio file."""
        if not path.exists():
            return
        
        try:
            ext = path.suffix.lower()
            if ext == '.mp3':
                AudioProcessor._tag_mp3(path, meta, cover)
            elif ext == '.ogg':
                AudioProcessor._tag_ogg(path, meta, cover)
            elif ext == '.flac':
                AudioProcessor._tag_flac(path, meta, cover)
        except Exception as e:
            logging.exception(f"Failed to tag {path}: {e}")

    @staticmethod
    def _tag_mp3(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag MP3 file with metadata."""
        try:
            tags = EasyID3(str(path))
        except mutagen.id3.ID3NoHeaderError:
            tags = EasyID3()
        
        tags['title'] = path.stem
        tags['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        tags['album'] = meta.title
        tags['organization'] = meta.circle
        tags.save(str(path))
        
        if cover and cover.exists():
            try:
                mime = mimetypes.guess_type(str(cover))[0] or 'image/jpeg'
                audio = MP3(str(path), ID3=ID3)
                with open(cover, 'rb') as c:
                    audio.tags.add(APIC(
                        encoding=3,
                        mime=mime,
                        type=3,
                        desc='Cover',
                        data=c.read()
                    ))
                audio.save()
            except Exception:
                pass

    @staticmethod
    def _tag_ogg(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag OGG file with metadata."""
        try:
            tags = OggVorbis(str(path))
        except mutagen.MutagenError:
            tags = OggVorbis()
        
        tags['title'] = path.stem
        tags['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        tags['album'] = meta.title
        tags['organization'] = meta.circle
        tags.save(str(path))  # always pass path explicitly to avoid ValueError

    @staticmethod
    def _tag_flac(path: Path, meta: WorkMetadata, cover: Optional[Path]) -> None:
        """Tag FLAC file with metadata."""
        audio = FLAC(str(path))
        audio['title'] = path.stem
        audio['artist'] = ", ".join(meta.cv) if meta.cv else "Unknown"
        audio['album'] = meta.title
        audio['organization'] = meta.circle
        
        if cover and cover.exists():
            mime = mimetypes.guess_type(str(cover))[0] or 'image/jpeg'
            picture = Picture()
            picture.type = 3
            picture.mime = mime
            with open(cover, 'rb') as c:
                picture.data = c.read()
            audio.clear_pictures()
            audio.add_picture(picture)
        
        audio.save()
