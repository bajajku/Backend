"""Google Cloud Storage client wrapper with local mode support."""

import json
from pathlib import Path
from typing import Optional

import structlog

from app.config import Settings
from app.models.schemas import ModelManifest

logger = structlog.get_logger()


class GCSClient:
    """Wrapper for Google Cloud Storage operations with local mode support."""

    def __init__(self, settings: Settings):
        """Initialize GCS client with settings."""
        self.settings = settings
        self.local_mode = settings.local_mode
        self.bucket_name = settings.gcs_bucket_name
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Get or create GCS client (only in cloud mode)."""
        if self.local_mode:
            return None

        if self._client is None:
            from google.cloud import storage
            self._client = storage.Client()
            logger.info("gcs_client_initialized", bucket=self.bucket_name)
        return self._client

    @property
    def bucket(self):
        """Get or create bucket reference (only in cloud mode)."""
        if self.local_mode:
            return None

        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    async def get_manifest(self) -> ModelManifest:
        """Fetch and parse the model manifest."""
        if self.local_mode:
            return await self._get_local_manifest()
        return await self._get_gcs_manifest()

    async def _get_local_manifest(self) -> ModelManifest:
        """Load manifest from local file."""
        manifest_path = Path(self.settings.local_models_path) / "manifest.json"

        try:
            content = manifest_path.read_text(encoding="utf-8")
            data = json.loads(content)
            manifest = ModelManifest.model_validate(data)
            logger.info(
                "local_manifest_loaded",
                path=str(manifest_path),
                model_count=len(manifest.models),
            )
            return manifest
        except FileNotFoundError:
            logger.error("local_manifest_not_found", path=str(manifest_path))
            raise
        except Exception as e:
            logger.error("local_manifest_load_failed", error=str(e))
            raise

    async def _get_gcs_manifest(self) -> ModelManifest:
        """Fetch manifest from GCS."""
        blob = self.bucket.blob("manifest.json")

        try:
            content = blob.download_as_text()
            data = json.loads(content)
            manifest = ModelManifest.model_validate(data)
            logger.info("gcs_manifest_loaded", model_count=len(manifest.models))
            return manifest
        except Exception as e:
            logger.error("gcs_manifest_load_failed", error=str(e))
            raise

    async def upload_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Upload audio file and return URL.

        In local mode, saves to local_models/audio/ directory.
        In cloud mode, uploads to GCS.
        """
        if self.local_mode:
            return await self._save_local_audio(audio_bytes, filename)
        return await self._upload_gcs_audio(audio_bytes, filename)

    async def _save_local_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Save audio file locally."""
        audio_dir = Path(self.settings.local_models_path) / "audio"
        audio_dir.mkdir(exist_ok=True)

        audio_path = audio_dir / filename
        audio_path.write_bytes(audio_bytes)

        # Return a web URL for local testing (served via FastAPI mount)
        url = f"/static/audio/{filename}"
        logger.info("local_audio_saved", path=str(audio_path), url=url)
        return url

    async def _upload_gcs_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Upload audio file to GCS."""
        blob_path = f"audio/{filename}"
        blob = self.bucket.blob(blob_path)

        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
        blob.make_public()

        url = blob.public_url
        logger.info("gcs_audio_uploaded", path=blob_path, url=url)
        return url

    async def check_health(self) -> bool:
        """Check if storage is accessible."""
        if self.local_mode:
            manifest_path = Path(self.settings.local_models_path) / "manifest.json"
            return manifest_path.exists()

        try:
            self.bucket.exists()
            return True
        except Exception as e:
            logger.error("gcs_health_check_failed", error=str(e))
            return False
