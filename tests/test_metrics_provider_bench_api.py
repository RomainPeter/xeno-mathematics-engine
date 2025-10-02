import os

from pefc.metrics.providers import BenchAPIClient


def test_bench_api_offline_mode():
    """Test BenchAPIClient in offline mode."""
    # Set offline mode
    os.environ["BENCH_API_OFFLINE"] = "1"

    try:
        client = BenchAPIClient(
            base_url="https://api.example.com",
            project_id="test-project",
            token="test-token",
        )

        # Should yield no documents in offline mode
        docs = list(client.iter_docs())
        assert len(docs) == 0

        # Test describe
        desc = client.describe()
        assert desc["kind"] == "bench_api"
        assert desc["base_url"] == "https://api.example.com"
        assert desc["project_id"] == "test-project"

    finally:
        # Clean up environment
        if "BENCH_API_OFFLINE" in os.environ:
            del os.environ["BENCH_API_OFFLINE"]


def test_bench_api_describe():
    """Test BenchAPIClient describe method."""
    client = BenchAPIClient(
        base_url="https://api.example.com",
        project_id="test-project",
        token="test-token",
        params={"since": "2025-01-01"},
    )

    desc = client.describe()
    assert desc["kind"] == "bench_api"
    assert desc["base_url"] == "https://api.example.com"
    assert desc["project_id"] == "test-project"


def test_bench_api_no_token():
    """Test BenchAPIClient without token."""
    client = BenchAPIClient(
        base_url="https://api.example.com",
        project_id="test-project",
        token=None,
    )

    # Should not crash
    desc = client.describe()
    assert desc["kind"] == "bench_api"


def test_bench_api_with_env_token():
    """Test BenchAPIClient with token from environment."""
    os.environ["BENCH_API_TOKEN"] = "env-token"

    try:
        client = BenchAPIClient(
            base_url="https://api.example.com",
            project_id="test-project",
            token=None,  # Should use env token
        )

        # Should not crash
        desc = client.describe()
        assert desc["kind"] == "bench_api"

    finally:
        # Clean up environment
        if "BENCH_API_TOKEN" in os.environ:
            del os.environ["BENCH_API_TOKEN"]


def test_bench_api_custom_params():
    """Test BenchAPIClient with custom parameters."""
    client = BenchAPIClient(
        base_url="https://api.example.com",
        project_id="test-project",
        token="test-token",
        params={"since": "2025-01-01", "limit": 100},
        timeout=30.0,
        page_size=1000,
    )

    # Should not crash
    desc = client.describe()
    assert desc["kind"] == "bench_api"
