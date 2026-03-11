"""Tests for Phase 4: MCP server logging wiring.

Verifies that the MCP server uses setup_logging_from_env() instead of
logging.basicConfig(), and that env var parsing is handled by the shared
helper in core.logging.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from unittest.mock import patch

import pytest

from linkedin_spider.core.logging import NAMESPACE


class TestMcpServerLoggingWiring:
    """Verify that mcp/server.py uses setup_logging instead of basicConfig."""

    @pytest.fixture(autouse=True)
    def _clean_logger(self) -> Generator[None, None, None]:
        """Reset namespace logger before/after each test."""
        logger = logging.getLogger(NAMESPACE)
        original_handlers = list(logger.handlers)
        original_level = logger.level
        original_propagate = logger.propagate
        yield
        logger.handlers[:] = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate

    def test_no_basic_config_in_server_module(self) -> None:
        """Ensure logging.basicConfig is not called at module level."""
        import inspect

        import linkedin_spider.mcp.server as server_mod

        source = inspect.getsource(server_mod)
        assert "basicConfig" not in source, (
            "logging.basicConfig should be removed from mcp/server.py"
        )

    def test_setup_logging_import_exists(self) -> None:
        """Verify that server module imports setup_logging."""
        import linkedin_spider.mcp.server as server_mod

        # The module should have access to setup_logging via import
        source = __import__("inspect").getsource(server_mod)
        assert "setup_logging" in source

    def test_serve_calls_setup_logging_from_env(self) -> None:
        """Verify that serve() calls setup_logging_from_env before initializing the scraper."""
        with (
            patch("linkedin_spider.mcp.server.setup_logging_from_env") as mock_setup,
            patch("linkedin_spider.mcp.server._initialize_scraper"),
            patch("linkedin_spider.mcp.server.mcp_app"),
        ):
            mock_setup.return_value = logging.getLogger(NAMESPACE)
            from linkedin_spider.mcp.server import serve

            with contextlib.suppress(SystemExit, Exception):
                serve(transport="stdio")

            mock_setup.assert_called_once()

    def test_serve_delegates_env_parsing_to_shared_helper(self) -> None:
        """Verify serve() does not inline env var parsing -- it delegates to setup_logging_from_env."""
        import inspect

        import linkedin_spider.mcp.server as server_mod

        source = inspect.getsource(server_mod.serve)
        # The serve function should NOT contain inline LOG_JSON parsing
        assert 'in ("true", "1", "yes")' not in source, (
            "serve() should delegate env var parsing to setup_logging_from_env"
        )

    def test_urllib3_not_silenced_at_module_level(self) -> None:
        """Verify urllib3 silencing is not done at module level (handled by setup_logging)."""
        import inspect

        import linkedin_spider.mcp.server as server_mod

        source = inspect.getsource(server_mod)
        # The standalone line should be removed; setup_logging handles it
        assert 'getLogger("urllib3.connectionpool")' not in source

    def test_logger_still_uses_namespace(self) -> None:
        """Verify the module logger is still a child of the linkedin_spider namespace."""
        from linkedin_spider.mcp.server import logger

        assert logger.name.startswith(NAMESPACE)


class TestSetupLoggingFromEnvIntegration:
    """Integration tests verifying env vars flow through setup_logging_from_env to setup_logging.

    These tests exercise the real setup_logging_from_env (no mocking of
    core.logging), confirming that environment variables produce the
    expected logger configuration.
    """

    @pytest.fixture(autouse=True)
    def _clean_logger(self) -> Generator[None, None, None]:
        """Reset namespace logger before/after each test."""
        logger = logging.getLogger(NAMESPACE)
        original_handlers = list(logger.handlers)
        original_level = logger.level
        original_propagate = logger.propagate
        yield
        logger.handlers[:] = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate

    def test_log_level_env_sets_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import setup_logging_from_env

        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        assert logger.level == logging.DEBUG

    def test_log_json_true_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import JSONFormatter, setup_logging_from_env

        monkeypatch.setenv("LOG_JSON", "true")
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_log_json_one_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import JSONFormatter, setup_logging_from_env

        monkeypatch.setenv("LOG_JSON", "1")
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_log_json_yes_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import JSONFormatter, setup_logging_from_env

        monkeypatch.setenv("LOG_JSON", "yes")
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_log_json_defaults_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import JSONFormatter, setup_logging_from_env

        monkeypatch.delenv("LOG_JSON", raising=False)
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        assert not isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_log_file_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
        import tempfile

        from linkedin_spider.core.logging import setup_logging_from_env

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = f"{tmpdir}/test.log"
            monkeypatch.setenv("LOG_FILE", log_path)
            setup_logging_from_env()
            logger = logging.getLogger(NAMESPACE)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1

    def test_log_file_defaults_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import setup_logging_from_env

        monkeypatch.delenv("LOG_FILE", raising=False)
        setup_logging_from_env()
        logger = logging.getLogger(NAMESPACE)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_explicit_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.core.logging import setup_logging_from_env

        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        setup_logging_from_env(level="DEBUG")
        logger = logging.getLogger(NAMESPACE)
        assert logger.level == logging.DEBUG
