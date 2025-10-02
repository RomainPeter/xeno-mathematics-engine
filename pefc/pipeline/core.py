from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pefc.errors import PackBuildError, SignatureError

log = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Context for pipeline execution."""

    cfg: Any  # Configuration object
    work_dir: Path
    out_dir: Path
    files: Dict[str, Path] = field(default_factory=dict)  # arcname -> src_path
    meta: Dict[str, Any] = field(default_factory=dict)  # step metadata
    status: str = "pending"  # pending, running, partial, failed, success
    errors: List[str] = field(default_factory=list)

    def add_file(self, arcname: str, src_path: Path) -> None:
        """Add file to context with deduplication check."""
        # Normalize arcname to POSIX
        arcname = arcname.replace("\\", "/")

        if arcname in self.files:
            raise PackBuildError(f"duplicate arcname: {arcname}")

        self.files[arcname] = src_path
        log.debug("pipeline: added file %s -> %s", arcname, src_path)

    def get_file_path(self, arcname: str) -> Optional[Path]:
        """Get source path for arcname."""
        return self.files.get(arcname)

    def add_meta(self, key: str, value: Any) -> None:
        """Add metadata to context."""
        self.meta[key] = value
        log.debug("pipeline: added meta %s = %s", key, value)

    def mark_partial(self, reason: str) -> None:
        """Mark pipeline as partial success."""
        self.status = "partial"
        self.errors.append(reason)
        log.warning("pipeline: partial success - %s", reason)

    def mark_failed(self, error: Exception) -> None:
        """Mark pipeline as failed."""
        self.status = "failed"
        self.errors.append(str(error))
        log.error("pipeline: failed - %s", error)


class PackStep:
    """Base class for pipeline steps."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, ctx: PipelineContext) -> None:
        """Execute the step."""
        raise NotImplementedError


class PipelineRunner:
    """Executes pipeline steps with error handling."""

    def __init__(self, cfg: Any):
        self.cfg = cfg

    def execute(self, steps: List[PackStep]) -> int:
        """Execute pipeline steps and return exit code."""
        work_dir = Path(self.cfg.pack.out_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        ctx = PipelineContext(
            cfg=self.cfg,
            work_dir=work_dir,
            out_dir=Path(self.cfg.pack.out_dir),
        )

        log.info("pipeline: starting execution with %d steps", len(steps))

        for i, step in enumerate(steps):
            step_name = step.__class__.__name__
            log.info("pipeline: step %d/%d - %s", i + 1, len(steps), step_name)

            start_time = time.time()

            try:
                # Publish step start event if available
                self._publish_event(
                    "step.start",
                    {
                        "step": step_name,
                        "step_index": i,
                        "config": step.config,
                    },
                )

                step.run(ctx)

                duration = time.time() - start_time
                log.info("pipeline: step %s completed in %.2fs", step_name, duration)

                # Publish step end event if available
                self._publish_event(
                    "step.end",
                    {
                        "step": step_name,
                        "step_index": i,
                        "duration": duration,
                        "status": "success",
                    },
                )

            except SignatureError as e:
                duration = time.time() - start_time
                log.warning(
                    "pipeline: step %s signature error in %.2fs: %s",
                    step_name,
                    duration,
                    e,
                )

                # Check if partial success is allowed for signatures
                if getattr(self.cfg.pack.sign, "allow_partial", False):
                    ctx.mark_partial(f"signature failed: {e}")
                    self._publish_event(
                        "step.end",
                        {
                            "step": step_name,
                            "step_index": i,
                            "duration": duration,
                            "status": "partial",
                            "error": str(e),
                        },
                    )
                else:
                    ctx.mark_failed(e)
                    self._publish_event(
                        "step.error",
                        {
                            "step": step_name,
                            "step_index": i,
                            "duration": duration,
                            "error": str(e),
                        },
                    )
                    return 1

            except Exception as e:
                duration = time.time() - start_time
                log.error("pipeline: step %s failed in %.2fs: %s", step_name, duration, e)
                ctx.mark_failed(e)

                self._publish_event(
                    "step.error",
                    {
                        "step": step_name,
                        "step_index": i,
                        "duration": duration,
                        "error": str(e),
                    },
                )
                return 1

        # Final status
        if ctx.status == "partial":
            log.info("pipeline: completed with partial success")
            self._publish_event("pipeline.end", {"status": "partial", "errors": ctx.errors})
            return 20  # Partial success
        elif ctx.status == "failed":
            log.error("pipeline: failed")
            self._publish_event("pipeline.end", {"status": "failed", "errors": ctx.errors})
            return 1
        else:
            log.info("pipeline: completed successfully")
            self._publish_event("pipeline.end", {"status": "success"})
            return 0

    def _publish_event(self, event: str, payload: Dict[str, Any]) -> None:
        """Publish event if event system is available."""
        try:
            from pefc.events import publish

            publish(event, payload)
        except ImportError:
            # Event system not available, noop
            pass
