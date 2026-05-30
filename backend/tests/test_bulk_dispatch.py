import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services import bulk_dispatch


def test_celery_worker_available_false_when_disabled() -> None:
    bulk_dispatch.reset_celery_availability_cache()
    with patch("app.services.bulk_dispatch.get_settings") as settings:
        settings.return_value.use_celery_bulk = False
        assert asyncio.run(bulk_dispatch.celery_worker_available()) is False


def test_celery_worker_available_false_without_redis() -> None:
    bulk_dispatch.reset_celery_availability_cache()
    with (
        patch("app.services.bulk_dispatch.get_settings") as settings,
        patch(
            "app.services.bulk_dispatch.redis_reachable",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        settings.return_value.use_celery_bulk = True
        assert asyncio.run(bulk_dispatch.celery_worker_available()) is False


def test_enqueue_bulk_zip_uses_background_when_celery_unavailable() -> None:
    bulk_dispatch.reset_celery_availability_cache()
    background = MagicMock()
    runner = AsyncMock()

    with patch(
        "app.services.bulk_dispatch.celery_worker_available",
        new_callable=AsyncMock,
        return_value=False,
    ):
        mode = asyncio.run(
            bulk_dispatch.enqueue_bulk_zip(
                job_id=uuid4(),
                zip_path=Path("test.zip"),
                background=background,
                background_runner=runner,
            )
        )
    assert mode == "background"
    background.add_task.assert_called_once()
