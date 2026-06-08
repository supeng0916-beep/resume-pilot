from __future__ import annotations

import shutil
from pathlib import Path

from main import write_report_output


def test_write_report_output_creates_parent_directories() -> None:
    output_dir = Path("data/test_outputs/pytest_cli_output")
    output_path = output_dir / "reports" / "batch_report.md"

    try:
        write_report_output(str(output_path), "# 批量候选人评估汇总\n\n- 张三")

        assert output_path.read_text(encoding="utf-8").startswith("# 批量候选人评估汇总")
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
