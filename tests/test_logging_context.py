import json

from pefc.logging import (
    clear_context,
    get_context,
    get_logger,
    init_logging,
    set_context,
    update_context,
)


def test_context_set_and_get():
    """Test setting and getting context."""
    clear_context()

    set_context(run_id="R123", step="ComputeMerkle")
    context = get_context()

    assert context["run_id"] == "R123"
    assert context["step"] == "ComputeMerkle"


def test_context_update():
    """Test updating context."""
    clear_context()

    set_context(run_id="R123")
    update_context(step="ComputeMerkle")

    context = get_context()
    assert context["run_id"] == "R123"
    assert context["step"] == "ComputeMerkle"


def test_context_clear():
    """Test clearing context."""
    set_context(run_id="R123", step="ComputeMerkle")
    clear_context()

    context = get_context()
    assert not context


def test_context_in_logs(capsys):
    """Test that context appears in logs."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    set_context(run_id="R123", step="ComputeMerkle", pack_version="v1.0.0")
    logger.info("processing")

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["context"]["run_id"] == "R123"
    assert log_entry["context"]["step"] == "ComputeMerkle"
    assert log_entry["context"]["pack_version"] == "v1.0.0"


def test_context_partial_update(capsys):
    """Test partial context updates."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    set_context(run_id="R123", step="ComputeMerkle")
    logger.info("step 1")

    update_context(step="BuildManifest")
    logger.info("step 2")

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    # First log
    log1 = json.loads(lines[0])
    assert log1["context"]["run_id"] == "R123"
    assert log1["context"]["step"] == "ComputeMerkle"

    # Second log
    log2 = json.loads(lines[1])
    assert log2["context"]["run_id"] == "R123"
    assert log2["context"]["step"] == "BuildManifest"


def test_context_thread_safety():
    """Test that context is thread-local."""
    import threading
    import time

    clear_context()

    def worker(thread_id):
        set_context(thread_id=thread_id, step=f"step_{thread_id}")
        time.sleep(0.1)  # Let other threads run
        context = get_context()
        assert context["thread_id"] == thread_id
        assert context["step"] == f"step_{thread_id}"

    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Main thread context should be empty
    context = get_context()
    assert not context
