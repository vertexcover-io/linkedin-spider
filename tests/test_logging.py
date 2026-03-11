"""Unit tests for the core logging module."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import pytest

from linkedin_spider.core.logging import (
    NAMESPACE,
    JSONFormatter,
    SpiderLoggerAdapter,
    _logging_context,
    get_logging_context,
    set_logging_context,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _clean_logging_state() -> Any:
    """Reset logging state before and after each test."""
    # Clear context
    _logging_context.clear()
    # Clear handlers on namespace logger and reset propagation
    logger = logging.getLogger(NAMESPACE)
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)
    logger.propagate = True
    yield
    _logging_context.clear()
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)
    logger.propagate = True


class TestSetupLogging:
    """Tests for setup_logging() function."""

    def test_returns_namespace_logger(self) -> None:
        logger = setup_logging()
        assert logger.name == NAMESPACE

    def test_default_level_is_info(self) -> None:
        logger = setup_logging()
        assert logger.level == logging.INFO

    def test_sets_debug_level(self) -> None:
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_sets_warning_level(self) -> None:
        logger = setup_logging(level="WARNING")
        assert logger.level == logging.WARNING

    def test_case_insensitive_level(self) -> None:
        logger = setup_logging(level="debug")
        assert logger.level == logging.DEBUG

    def test_invalid_level_falls_back_to_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = setup_logging(level="INVALID")
        assert logger.level == logging.INFO
        captured = capsys.readouterr()
        assert "Invalid log level" in captured.err

    def test_has_stderr_handler(self) -> None:
        logger = setup_logging()
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_idempotency_no_duplicate_handlers(self) -> None:
        setup_logging()
        logger = setup_logging()
        assert len(logger.handlers) == 1

    def test_no_propagation(self) -> None:
        logger = setup_logging()
        assert logger.propagate is False

    def test_json_output_uses_json_formatter(self) -> None:
        logger = setup_logging(json_output=True)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_text_output_uses_standard_formatter(self) -> None:
        logger = setup_logging(json_output=False)
        formatter = logger.handlers[0].formatter
        assert formatter is not None
        assert not isinstance(formatter, JSONFormatter)

    def test_log_file_adds_file_handler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=str(log_path))
            assert len(logger.handlers) == 2
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1

    def test_log_file_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "nested" / "dir" / "test.log"
            setup_logging(log_file=str(log_path))
            assert log_path.parent.exists()

    def test_silences_urllib3_above_debug(self) -> None:
        setup_logging(level="INFO")
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        assert urllib3_logger.level == logging.ERROR

    def test_does_not_silence_urllib3_at_debug(self) -> None:
        urllib3_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_logger.setLevel(logging.NOTSET)
        setup_logging(level="DEBUG")
        assert urllib3_logger.level != logging.ERROR


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_output_is_valid_json(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello world",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed

    def test_level_and_logger_values(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.scrapers.profile",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Something happened",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "WARNING"
        assert parsed["logger"] == "linkedin_spider.scrapers.profile"
        assert parsed["message"] == "Something happened"

    def test_includes_extra_context_fields(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=None,
            exc_info=None,
        )
        record.session_id = "abc123"
        record.scraper = "profile"
        record.target_url = "https://linkedin.com/in/test"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["session_id"] == "abc123"
        assert parsed["scraper"] == "profile"
        assert parsed["target_url"] == "https://linkedin.com/in/test"

    def test_omits_missing_extra_fields(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "session_id" not in parsed
        assert "scraper" not in parsed
        assert "target_url" not in parsed

    def test_handles_non_serializable_extras(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="linkedin_spider.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=None,
            exc_info=None,
        )
        record.session_id = object()
        output = formatter.format(record)
        # Should not raise; default=str handles it
        parsed = json.loads(output)
        assert "session_id" in parsed


class TestSpiderLoggerAdapter:
    """Tests for SpiderLoggerAdapter class."""

    def test_injects_extra_fields(self) -> None:
        logger = logging.getLogger("linkedin_spider.test.adapter")
        adapter = SpiderLoggerAdapter(logger, {"scraper": "profile", "session_id": "test-session"})
        _msg, kwargs = adapter.process("hello", {})
        assert kwargs["extra"]["scraper"] == "profile"
        assert kwargs["extra"]["session_id"] == "test-session"

    def test_call_site_extra_overrides_adapter(self) -> None:
        logger = logging.getLogger("linkedin_spider.test.adapter2")
        adapter = SpiderLoggerAdapter(logger, {"scraper": "profile"})
        _msg, kwargs = adapter.process("hello", {"extra": {"scraper": "company"}})
        assert kwargs["extra"]["scraper"] == "company"

    def test_reads_session_id_from_module_context(self) -> None:
        set_logging_context(session_id="ctx-session")
        logger = logging.getLogger("linkedin_spider.test.adapter3")
        adapter = SpiderLoggerAdapter(logger, {"scraper": "search"})
        _msg, kwargs = adapter.process("hello", {})
        assert kwargs["extra"]["session_id"] == "ctx-session"

    def test_adapter_session_id_overrides_context(self) -> None:
        set_logging_context(session_id="ctx-session")
        logger = logging.getLogger("linkedin_spider.test.adapter4")
        adapter = SpiderLoggerAdapter(logger, {"session_id": "adapter-session"})
        _msg, kwargs = adapter.process("hello", {})
        assert kwargs["extra"]["session_id"] == "adapter-session"

    def test_defaults_to_unknown_session_id(self) -> None:
        logger = logging.getLogger("linkedin_spider.test.adapter5")
        adapter = SpiderLoggerAdapter(logger, {"scraper": "test"})
        _msg, kwargs = adapter.process("hello", {})
        assert kwargs["extra"]["session_id"] == "unknown"


class TestLoggingContext:
    """Tests for module-level context management."""

    def test_set_and_get_roundtrip(self) -> None:
        set_logging_context(session_id="abc")
        ctx = get_logging_context()
        assert ctx["session_id"] == "abc"

    def test_get_returns_copy(self) -> None:
        set_logging_context(session_id="abc")
        ctx = get_logging_context()
        ctx["session_id"] = "modified"
        assert get_logging_context()["session_id"] == "abc"

    def test_empty_context_initially(self) -> None:
        ctx = get_logging_context()
        assert ctx == {}

    def test_multiple_keys(self) -> None:
        set_logging_context(session_id="s1", scraper="profile")
        ctx = get_logging_context()
        assert ctx["session_id"] == "s1"
        assert ctx["scraper"] == "profile"


class TestBaseScraperLogAction:
    """Tests for BaseScraper.log_action() level mapping (Phase 2)."""

    @pytest.fixture()
    def scraper(self) -> Any:
        """Create a BaseScraper with mocked dependencies."""
        from unittest.mock import MagicMock

        from linkedin_spider.scrapers.base import BaseScraper

        driver = MagicMock()
        wait = MagicMock()
        human_behavior = MagicMock()
        tracking_handler = MagicMock()
        return BaseScraper(driver, wait, human_behavior, tracking_handler)

    def test_error_action_emits_at_error_level(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("ERROR", "something broke")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.ERROR

    def test_warning_action_emits_at_warning_level(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("WARNING", "caution")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING

    def test_debug_action_emits_at_debug_level(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("DEBUG", "trace info")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.DEBUG

    def test_info_action_emits_at_info_level(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("INFO", "status update")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_success_action_emits_at_info_level(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("SUCCESS", "completed")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_unknown_action_defaults_to_info(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("UNKNOWN_ACTION", "something")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO

    def test_log_message_format(self, scraper: Any, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("INFO", "navigating")
        assert "[BaseScraper] INFO: navigating" in caplog.records[0].getMessage()

    def test_scraper_context_in_log_record(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("INFO", "test")
        record = caplog.records[0]
        assert getattr(record, "scraper", None) == "BaseScraper"

    def test_session_id_defaults_to_unknown(
        self, scraper: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG, logger="linkedin_spider.scrapers.base"):
            scraper.log_action("INFO", "test")
        record = caplog.records[0]
        assert getattr(record, "session_id", None) == "unknown"


class TestLogConfig:
    """Tests for LogConfig CLI dataclass."""

    def test_defaults_to_none(self) -> None:
        from linkedin_spider.cli.main import LogConfig

        config = LogConfig()
        assert config.log_level is None
        assert config.log_json is None
        assert config.log_file is None

    def test_accepts_explicit_values(self) -> None:
        from linkedin_spider.cli.main import LogConfig

        config = LogConfig(log_level="DEBUG", log_json=True, log_file="/tmp/test.log")
        assert config.log_level == "DEBUG"
        assert config.log_json is True
        assert config.log_file == "/tmp/test.log"


class TestConfigureLogging:
    """Tests for _configure_logging() CLI helper."""

    def test_explicit_level_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        config = LogConfig(log_level="DEBUG")
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert logger.level == logging.DEBUG

    def test_env_var_fallback_for_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert logger.level == logging.ERROR

    def test_default_level_is_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.delenv("LOG_LEVEL", raising=False)
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert logger.level == logging.INFO

    def test_explicit_json_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_JSON", "true")
        config = LogConfig(log_json=False)
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert not isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_env_var_fallback_for_json_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_JSON", "true")
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_env_var_json_accepts_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_JSON", "1")
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_env_var_json_accepts_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.setenv("LOG_JSON", "yes")
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_default_json_is_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.delenv("LOG_JSON", raising=False)
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        assert not isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_explicit_log_file_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import tempfile

        from linkedin_spider.cli.main import LogConfig, _configure_logging

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = f"{tmpdir}/env.log"
            explicit_path = f"{tmpdir}/explicit.log"
            monkeypatch.setenv("LOG_FILE", env_path)
            config = LogConfig(log_file=explicit_path)
            _configure_logging(config)
            logger = logging.getLogger(NAMESPACE)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            assert file_handlers[0].baseFilename == str(Path(explicit_path).resolve())

    def test_env_var_fallback_for_log_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import tempfile

        from linkedin_spider.cli.main import LogConfig, _configure_logging

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = f"{tmpdir}/env.log"
            monkeypatch.setenv("LOG_FILE", env_path)
            config = LogConfig()
            _configure_logging(config)
            logger = logging.getLogger(NAMESPACE)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            assert file_handlers[0].baseFilename == str(Path(env_path).resolve())

    def test_no_file_handler_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from linkedin_spider.cli.main import LogConfig, _configure_logging

        monkeypatch.delenv("LOG_FILE", raising=False)
        config = LogConfig()
        _configure_logging(config)
        logger = logging.getLogger(NAMESPACE)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0


class TestLinkedinSpiderSetsLoggingContext:
    """Tests for session_id logging context set during LinkedinSpider._initialize()."""

    def test_initialize_sets_session_id_in_logging_context(self) -> None:
        """After _initialize(), logging context should contain the driver manager's session_id."""
        from unittest.mock import MagicMock, patch

        from linkedin_spider.core.scraper import LinkedinSpider

        # We must prevent the real __init__ from running (it launches Chrome).
        # Instead, we instantiate without __init__ and call _initialize() with mocks.
        spider = LinkedinSpider.__new__(LinkedinSpider)

        # Set up minimal attributes that _initialize() depends on
        mock_driver = MagicMock()
        mock_driver_manager = MagicMock()
        mock_driver_manager.session_id = "test-session-42"
        mock_driver_manager.setup_driver.return_value = mock_driver
        mock_driver_manager.wait = MagicMock()
        mock_driver_manager.actions = MagicMock()

        spider.driver_manager = mock_driver_manager
        spider.config = MagicMock()
        spider._credentials = {"email": None, "password": None, "li_at_cookie": None}

        with (
            patch.object(spider, "_initialize_scrapers"),
            patch.object(spider, "_configure_anti_detection"),
            patch("linkedin_spider.core.scraper.AuthManager"),
        ):
            spider._initialize()

        ctx = get_logging_context()
        assert ctx["session_id"] == "test-session-42"

    def test_logging_context_session_id_matches_driver_manager(self) -> None:
        """The session_id in logging context must come from DriverManager, not be hardcoded."""
        from unittest.mock import MagicMock, patch

        from linkedin_spider.core.scraper import LinkedinSpider

        spider = LinkedinSpider.__new__(LinkedinSpider)

        mock_driver = MagicMock()
        mock_driver_manager = MagicMock()
        mock_driver_manager.session_id = "unique-abc-789"
        mock_driver_manager.setup_driver.return_value = mock_driver
        mock_driver_manager.wait = MagicMock()
        mock_driver_manager.actions = MagicMock()

        spider.driver_manager = mock_driver_manager
        spider.config = MagicMock()
        spider._credentials = {"email": None, "password": None, "li_at_cookie": None}

        with (
            patch.object(spider, "_initialize_scrapers"),
            patch.object(spider, "_configure_anti_detection"),
            patch("linkedin_spider.core.scraper.AuthManager"),
        ):
            spider._initialize()

        ctx = get_logging_context()
        assert ctx["session_id"] == "unique-abc-789"

    def test_context_set_before_initialize_scrapers(self) -> None:
        """set_logging_context must be called before _initialize_scrapers."""
        from unittest.mock import MagicMock, patch

        from linkedin_spider.core.scraper import LinkedinSpider

        spider = LinkedinSpider.__new__(LinkedinSpider)

        mock_driver = MagicMock()
        mock_driver_manager = MagicMock()
        mock_driver_manager.session_id = "order-check"
        mock_driver_manager.setup_driver.return_value = mock_driver
        mock_driver_manager.wait = MagicMock()
        mock_driver_manager.actions = MagicMock()

        spider.driver_manager = mock_driver_manager
        spider.config = MagicMock()
        spider._credentials = {"email": None, "password": None, "li_at_cookie": None}

        call_order: list[str] = []

        def track_set_context(**kwargs: str) -> None:
            call_order.append("set_logging_context")
            # Actually set it so other assertions work
            set_logging_context(**kwargs)

        def track_init_scrapers() -> None:
            call_order.append("_initialize_scrapers")

        with (
            patch(
                "linkedin_spider.core.scraper.set_logging_context",
                side_effect=track_set_context,
            ),
            patch.object(spider, "_initialize_scrapers", side_effect=track_init_scrapers),
            patch.object(spider, "_configure_anti_detection"),
            patch("linkedin_spider.core.scraper.AuthManager"),
        ):
            spider._initialize()

        assert call_order.index("set_logging_context") < call_order.index("_initialize_scrapers"), (
            "set_logging_context must be called before _initialize_scrapers"
        )
