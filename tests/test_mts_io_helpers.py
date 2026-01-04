import tempfile
from pathlib import Path
from cogstim.mts_helpers.io import build_basename, SummaryWriter


def test_build_basename_variants():
    name1 = build_basename(2, 3, 0, equalized=False, version_tag=None)
    assert name1.startswith("img_2_3_0")
    assert "equalized" not in name1

    name2 = build_basename(5, 5, 2, equalized=True, version_tag="v1")
    assert name2.startswith("img_5_5_2_equalized_v1")


def test_summary_writer_write_csv(tmp_path):
    outdir = tmp_path / "summary_dir"
    writer = SummaryWriter(str(outdir))

    # Add a couple of rows
    writer.add(2, 3, 100.0, 110.0, equalized=True)
    writer.add(4, 1, 200.0, 50.0, equalized=False)

    # Write CSV and validate file exists and contents
    writer.write_csv()
    csv_path = outdir / "summary.csv"
    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8")
    assert "num1" in content
    assert "num2" in content
    assert "equalized" in content
    # Ensure rows were written
    assert "2" in content
    assert "4" in content

