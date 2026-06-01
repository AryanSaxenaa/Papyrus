import asyncio
from unittest.mock import AsyncMock, patch

from app.services import background_dispatch
from app.services.celery_heartbeat import heartbeat_key, write_heartbeat_sync


def test_heartbeat_key_includes_queue() -> None:
    assert heartbeat_key("audits-production") == "papyrus:celery:heartbeat:audits-production"


def test_celery_worker_available_true_when_heartbeat_present() -> None:
    background_dispatch.reset_celery_availability_cache()
    with (
        patch("app.services.background_dispatch.get_settings") as settings,
        patch(
            "app.services.background_dispatch.redis_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.celery_heartbeat.heartbeat_present",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("app.worker.celery_app") as celery_app,
    ):
        settings.return_value.celery_background_enabled.return_value = True
        settings.return_value.audit_queue_name.return_value = "audits-production"
        celery_app.control.inspect.return_value.ping.return_value = None
        celery_app.control.inspect.return_value.active_queues.return_value = None
        assert asyncio.run(background_dispatch.celery_worker_available()) is True
