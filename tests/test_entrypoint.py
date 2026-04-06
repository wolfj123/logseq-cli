"""Verify the CLI entry point is importable as an installed package."""


def test_src_package_is_importable():
    import src
    assert src is not None


def test_cli_main_is_importable():
    from src.cli.main import app
    assert app is not None


def test_logseq_service_is_importable():
    from src.logseq_service import LogseqService
    assert LogseqService is not None
