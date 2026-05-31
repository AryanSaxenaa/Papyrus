import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services import background_dispatch


def test_celery_worker_available_false_when_disabled() -> None:
    background_dispatch.reset_celery_availability_cache()
    with patch("app.services.background_dispatch.get_settings") as settings:
        settings.return_value.celery_background_enabled.return_value = False
        assert asyncio.run(background_dispatch.celery_worker_available()) is False


def test_celery_worker_available_false_without_redis() -> None:
    background_dispatch.reset_celery_availability_cache()
    with (
        patch("app.services.background_dispatch.get_settings") as settings,
        patch(
            "app.services.background_dispatch.redis_reachable",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        settings.return_value.celery_background_enabled.return_value = True
        assert asyncio.run(background_dispatch.celery_worker_available()) is False


def test_enqueue_bulk_zip_uses_background_when_celery_unavailable() -> None:
    background_dispatch.reset_celery_availability_cache()
    background = MagicMock()

    with patch(
        "app.services.background_dispatch.celery_worker_available",
        new_callable=AsyncMock,
        return_value=False,
    ):
        mode = asyncio.run(
            background_dispatch.enqueue_bulk_zip(
                job_id=uuid4(),
                storage_key="uploads/bulk/test.zip",
                background=background,
            )
        )
    assert mode == "background"
    background.add_task.assert_called_once()
