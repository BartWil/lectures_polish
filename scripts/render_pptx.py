#!/usr/bin/env python3
"""Renderuje każdy slajd PPTX do PNG przez natywny Microsoft PowerPoint.

Skrypt jest narzędziem diagnostycznym: nie zmienia prezentacji wejściowej, nie
wykonuje OCR ani nie interpretuje treści. Wszystkie wyniki zapisuje wyłącznie w
``imports_working/<nazwa-prezentacji>/``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKING_ROOT = PROJECT_ROOT / "imports_working"
PNG_PATTERN = re.compile(r"^slide_(\d{3})\.png$")


def sha256_file(path: Path) -> str:
    """Zwraca SHA-256 pliku bez wczytywania go w całości do pamięci."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_for_powershell(value: str) -> str:
    """Zwraca literal PowerShell dla tekstu, zachowując znaki Unicode."""
    return "'" + value.replace("'", "''") + "'"


def invoke_powerpoint(source: Path, output_dir: Path, width: int) -> tuple[dict[str, Any], list[dict[str, Any]], str, int]:
    """Uruchamia ukryty PowerPoint COM i zapisuje po jednym JSON na slajd."""
    script = f"""
$ErrorActionPreference = 'Stop'
$app = $null
$presentation = $null
try {{
    $app = New-Object -ComObject PowerPoint.Application
    $presentation = $app.Presentations.Open({json_for_powershell(str(source))}, $true, $false, $false)
    $slideWidth = [double]$presentation.PageSetup.SlideWidth
    $slideHeight = [double]$presentation.PageSetup.SlideHeight
    $renderHeight = [int][Math]::Round({width} * $slideHeight / $slideWidth)
    [PSCustomObject]@{{
        event = 'metadata'
        slide_count = [int]$presentation.Slides.Count
        slide_width_points = $slideWidth
        slide_height_points = $slideHeight
        target_width_px = {width}
        target_height_px = $renderHeight
    }} | ConvertTo-Json -Compress
    foreach ($slide in $presentation.Slides) {{
        $slideNumber = [int]$slide.SlideIndex
        $pngName = 'slide_{{0:D3}}.png' -f $slideNumber
        $pngPath = Join-Path {json_for_powershell(str(output_dir))} $pngName
        try {{
            $slide.Export($pngPath, 'PNG', {width}, $renderHeight)
            [PSCustomObject]@{{event='slide'; slide_number=$slideNumber; png_filename=$pngName; status='success'; error=$null}} | ConvertTo-Json -Compress
        }} catch {{
            [PSCustomObject]@{{event='slide'; slide_number=$slideNumber; png_filename=$pngName; status='error'; error=$_.Exception.Message}} | ConvertTo-Json -Compress
        }}
    }}
}} catch {{
    [PSCustomObject]@{{event='fatal'; error=$_.Exception.Message}} | ConvertTo-Json -Compress
    exit 1
}} finally {{
    if ($null -ne $presentation) {{
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }}
    if ($null -ne $app) {{
        $app.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
    }}
}}
""".strip()
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        text=True,
        capture_output=True,
        check=False,
    )

    metadata: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") == "metadata":
            metadata = row
        elif row.get("event") == "slide":
            records.append(row)
        elif row.get("event") == "fatal":
            metadata["fatal_error"] = row.get("error")
    diagnostics = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    return metadata, records, diagnostics, completed.returncode


def inspect_png(path: Path) -> tuple[int, int, int, str]:
    """Sprawdza czy obraz jest poprawnym PNG i zwraca jego metadane."""
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        width, height = image.size
    return width, height, path.stat().st_size, sha256_file(path)


def create_contact_sheets(rendered_dir: Path, destination: Path, columns: int, rows: int) -> list[str]:
    """Tworzy proste, ponumerowane plansze po ``columns * rows`` miniatur."""
    destination.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (path for path in rendered_dir.iterdir() if PNG_PATTERN.match(path.name)),
        key=lambda path: int(PNG_PATTERN.match(path.name).group(1)),  # type: ignore[union-attr]
    )
    if not files:
        return []

    thumb_width, thumb_height, label_height, padding = 360, 203, 30, 12
    cell_width, cell_height = thumb_width + 2 * padding, thumb_height + label_height + 2 * padding
    font = ImageFont.load_default()
    outputs: list[str] = []
    for index in range(0, len(files), columns * rows):
        group = files[index : index + columns * rows]
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(sheet)
        for offset, png_path in enumerate(group):
            row, column = divmod(offset, columns)
            x, y = column * cell_width + padding, row * cell_height + padding
            with Image.open(png_path) as original:
                preview = original.convert("RGB")
                preview.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            image_x = x + (thumb_width - preview.width) // 2
            image_y = y + (thumb_height - preview.height) // 2
            sheet.paste(preview, (image_x, image_y))
            draw.rectangle((x - 1, y - 1, x + thumb_width, y + thumb_height), outline="gray")
            draw.text((x, y + thumb_height + 7), png_path.stem.replace("_", " "), fill="black", font=font)
        output = destination / f"contact_sheet_{index // (columns * rows) + 1:03}.png"
        sheet.save(output, format="PNG", optimize=True)
        outputs.append(output.name)
    return outputs


def prepare_output(working_dir: Path, overwrite: bool) -> tuple[Path, Path, Path]:
    """Tworzy katalogi wynikowe, nigdy nie usuwając danych wejściowych PPTX."""
    working_dir.resolve().relative_to(WORKING_ROOT.resolve())
    rendered_dir = working_dir / "rendered_slides"
    contact_dir = working_dir / "contact_sheets"
    manifest = working_dir / "render_manifest.json"
    generated = [rendered_dir, contact_dir]
    existing = [path for path in generated if path.exists() and any(path.iterdir())]
    if (existing or manifest.exists()) and not overwrite:
        joined = ", ".join(str(path) for path in existing + ([manifest] if manifest.exists() else []))
        raise RuntimeError(f"Istnieją już wyniki renderowania ({joined}). Użyj --overwrite, aby odtworzyć tylko wyniki renderera.")
    if overwrite:
        for path in generated:
            if path.exists():
                shutil.rmtree(path)
        if manifest.exists():
            manifest.unlink()
    rendered_dir.mkdir(parents=True, exist_ok=True)
    return rendered_dir, contact_dir, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Renderuje PPTX do PNG przez Microsoft PowerPoint COM.")
    parser.add_argument("pptx", type=Path, help="lokalna ścieżka do prezentacji .pptx")
    parser.add_argument("--width", type=int, default=1920, help="docelowa szerokość PNG w pikselach (domyślnie: 1920)")
    parser.add_argument("--overwrite", action="store_true", help="odtwórz wyłącznie istniejące wyniki renderera")
    parser.add_argument("--columns", type=int, default=4, help="liczba kolumn contact sheet")
    parser.add_argument("--rows", type=int, default=3, help="liczba wierszy contact sheet")
    args = parser.parse_args()

    source = args.pptx.expanduser().resolve()
    if source.suffix.lower() != ".pptx" or not source.is_file():
        parser.error("argument pptx musi wskazywać istniejący plik .pptx")
    if args.width < 320 or args.columns < 1 or args.rows < 1:
        parser.error("szerokość musi wynosić co najmniej 320, a układ contact sheet co najmniej 1 × 1")

    working_dir = WORKING_ROOT / source.stem
    try:
        rendered_dir, contact_dir, manifest_path = prepare_output(working_dir, args.overwrite)
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))

    metadata, records, diagnostics, process_code = invoke_powerpoint(source, rendered_dir, args.width)
    slide_count = int(metadata.get("slide_count", 0))
    by_number = {int(record["slide_number"]): record for record in records if record.get("slide_number")}
    expected_height = int(metadata.get("target_height_px", 0))
    entries: list[dict[str, Any]] = []
    for slide_number in range(1, slide_count + 1):
        filename = f"slide_{slide_number:03}.png"
        record = by_number.get(slide_number, {})
        entry: dict[str, Any] = {
            "presentation_filename": source.name,
            "slide_number": slide_number,
            "png_filename": filename,
            "width_px": None,
            "height_px": None,
            "file_size_bytes": None,
            "sha256": None,
            "render_status": record.get("status", "error"),
            "error": record.get("error") or ("Brak wyniku eksportu dla slajdu." if not record else None),
        }
        png_path = rendered_dir / filename
        if entry["render_status"] == "success":
            try:
                width, height, size, digest = inspect_png(png_path)
                entry.update(width_px=width, height_px=height, file_size_bytes=size, sha256=digest)
                if width != args.width or height != expected_height or size == 0:
                    entry.update(render_status="error", error="PNG ma nieoczekiwany rozmiar, proporcje lub 0 B.")
            except (FileNotFoundError, OSError) as error:
                entry.update(render_status="error", error=f"Nie można otworzyć PNG: {error}")
        entries.append(entry)

    extra_pngs = sorted(path.name for path in rendered_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png" and path.name not in {entry["png_filename"] for entry in entries})
    contact_sheets = create_contact_sheets(rendered_dir, contact_dir, args.columns, args.rows)
    manifest = {
        "schema_version": "1.0",
        "rendered_at": datetime.now(UTC).isoformat(),
        "presentation": {
            "filename": source.name,
            "file_size_bytes": source.stat().st_size,
            "sha256": sha256_file(source),
            "slide_count": slide_count,
            "slide_width_points": metadata.get("slide_width_points"),
            "slide_height_points": metadata.get("slide_height_points"),
            "aspect_ratio": round(float(metadata.get("slide_width_points", 0)) / float(metadata.get("slide_height_points", 1)), 6),
        },
        "render": {
            "engine": "Microsoft PowerPoint COM / Slide.Export",
            "target_width_px": args.width,
            "target_height_px": expected_height,
            "powershell_exit_code": process_code,
        },
        "slides": entries,
        "validation": {
            "expected_slide_numbers": list(range(1, slide_count + 1)),
            "extra_png_files": extra_pngs,
            "contact_sheets": contact_sheets,
            "powershell_diagnostics": diagnostics,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [entry for entry in entries if entry["render_status"] != "success"]
    print(f"Prezentacja: {source.name}")
    print(f"Slajdy: {slide_count}; poprawne PNG: {slide_count - len(failed)}; błędy: {len(failed)}")
    print(f"PNG: {args.width} × {expected_height} px; contact sheets: {len(contact_sheets)}")
    print(f"Manifest: {manifest_path}")
    if not slide_count or process_code != 0 or failed or extra_pngs:
        print("Walidacja renderowania NIE powiodła się.", file=sys.stderr)
        return 1
    print("Walidacja renderowania zakończona sukcesem.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
