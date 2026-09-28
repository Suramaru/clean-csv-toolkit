#!/usr/bin/env python3
"""clean_csv.py — utilidad reproducible de limpieza de CSV (zero-dependency).

Muestra de trabajo v1 del "Paquete C — Data Tidy & Reproducible Script" definido en
el kit operativo (artifact art_064b7b14b5d3). Es un ENTREGABLE DE MUESTRA interno:
sin datos de terceros, sin red, sin credenciales y sin publicarse en ningun sitio.

Uso
---
    python clean_csv.py --in entrada.csv --out limpio.csv [--report informe.json]
    python clean_csv.py --selftest
    python clean_csv.py --version

Que hace (determinista)
-----------------------
  1. Normaliza cabeceras a snake_case ASCII (col_N si quedan vacias).
  2. Recorta espacios en cada celda.
  3. Elimina filas totalmente vacias.
  4. Elimina columnas totalmente vacias.
  5. Elimina filas duplicadas exactas (tras recorte), conservando la primera.
  6. Emite un informe JSON con contadores y cabeceras antes/despues.

Limites declarados
------------------
  - No infiere tipos de datos.
  - No trata encoding distinto de UTF-8.
  - No acepta ni procesa datos personales sensibles.
  - Es una muestra acotada, no un producto terminado ni una promesa de resultados.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time

__version__ = "1.0.0"


def normalize_header(name: str, index: int) -> str:
    """Devuelve una cabecera en snake_case ASCII; col_N si no queda nada util."""
    text = (name or "").strip().lower()
    text = re.sub(r"[^0-9a-z]+", "_", text)
    text = text.strip("_")
    if not text:
        text = f"col_{index + 1}"
    return text


def is_blank(value: object) -> bool:
    """True si el valor es None o solo espacios en blanco."""
    return value is None or str(value).strip() == ""


def _dedupe_headers(headers: list[str]) -> list[str]:
    """Evita cabeceras repetidas anadiendo sufijo _2, _3, ..."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for head in headers:
        if head in seen:
            seen[head] += 1
            out.append(f"{head}_{seen[head]}")
        else:
            seen[head] = 0
            out.append(head)
    return out


def process_text(text: str) -> dict:
    """Limpia el CSV dado como texto y devuelve {headers, rows, report}."""
    reader = csv.reader(io.StringIO(text))
    raw = list(reader)
    if not raw:
        return {
            "headers": [],
            "rows": [],
            "report": {
                "input_rows": 0,
                "output_rows": 0,
                "dropped_blank_rows": 0,
                "dropped_duplicate_rows": 0,
                "dropped_blank_cols": 0,
                "headers_before": [],
                "headers_after": [],
            },
        }

    input_rows = max(len(raw) - 1, 0)
    headers_trimmed = [str(h).strip() for h in raw[0]]
    body = [[str(c).strip() for c in row] for row in raw[1:]]

    # 3. eliminar filas totalmente vacias
    before_rows = len(body)
    body = [row for row in body if not all(is_blank(c) for c in row)]
    dropped_blank_rows = before_rows - len(body)

    # ancho = max(cabeceras, filas); rellenar/recortar filas
    width = max([len(headers_trimmed)] + [len(row) for row in body])
    norm_headers = [normalize_header(h, i) for i, h in enumerate(headers_trimmed)]
    while len(norm_headers) < width:
        norm_headers.append(f"col_{len(norm_headers) + 1}")
    norm_headers = _dedupe_headers(norm_headers)
    body = [row + [""] * (width - len(row)) for row in body]

    # 4. eliminar columnas totalmente vacias
    if body:
        keep = [i for i in range(width) if any(not is_blank(row[i]) for row in body)]
    else:
        keep = [i for i in range(width) if not is_blank(norm_headers[i])]
    dropped_blank_cols = width - len(keep)
    headers_out = [norm_headers[i] for i in keep]
    body = [[row[i] for i in keep] for row in body]

    # 5. eliminar filas duplicadas exactas (conservando la primera)
    seen: set[tuple[str, ...]] = set()
    deduped: list[list[str]] = []
    dropped_dups = 0
    for row in body:
        key = tuple(row)
        if key in seen:
            dropped_dups += 1
            continue
        seen.add(key)
        deduped.append(row)

    report = {
        "input_rows": input_rows,
        "output_rows": len(deduped),
        "dropped_blank_rows": dropped_blank_rows,
        "dropped_duplicate_rows": dropped_dups,
        "dropped_blank_cols": dropped_blank_cols,
        "headers_before": headers_trimmed,
        "headers_after": headers_out,
    }
    return {"headers": headers_out, "rows": deduped, "report": report}


def to_csv_text(headers: list[str], rows: list[list[str]]) -> str:
    """Serializa de forma determinista (LF) a texto CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def run(in_path: str, out_path: str, report_path: str | None) -> dict:
    """Procesa un fichero y escribe salida + informe. Devuelve el informe."""
    with open(in_path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    started = time.perf_counter()
    result = process_text(text)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(to_csv_text(result["headers"], result["rows"]))
    report = dict(result["report"])
    report["input_path"] = in_path
    report["output_path"] = out_path
    report["elapsed_ms"] = elapsed_ms
    if report_path:
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
    return report


# --------------------------------------------------------------------------- test

MESSY_SAMPLE = (
    " Name , Age ,Notes, City \n"
    "Alice , 30 ,, Madrid \n"
    "Bob , 25 ,, \n"
    "   , , ,   \n"
    "Carol , 40 ,,Lima\n"
    "Alice , 30 ,, Madrid \n"
)


def selftest() -> int:
    """Auto-test deterministico: no toca red, ficheros ni datos externos."""
    result = process_text(MESSY_SAMPLE)
    report = result["report"]
    expected = {
        "input_rows": 5,
        "output_rows": 3,
        "dropped_blank_rows": 1,
        "dropped_duplicate_rows": 1,
        "dropped_blank_cols": 1,
    }
    failures = [k for k, v in expected.items() if report.get(k) != v]

    checks = [
        ("headers_after == [name, age, city]", report["headers_after"] == ["name", "age", "city"]),
        ("primera fila == [Alice, 30, Madrid]", result["rows"][0] == ["Alice", "30", "Madrid"]),
        ("segunda fila == [Bob, 25, '']", result["rows"][1] == ["Bob", "25", ""]),
        ("tercera fila == [Carol, 40, Lima]", result["rows"][2] == ["Carol", "40", "Lima"]),
        ("contadores esperados", not failures),
    ]
    for label, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {label}")
    if failures:
        print(f"  contadores inesperados: {failures}; report={json.dumps(report, ensure_ascii=False)}")
        return 1
    # idempotencia: limpiar la salida no debe cambiar las filas
    second = process_text(to_csv_text(result["headers"], result["rows"]))
    if second["rows"] != result["rows"] or second["report"]["dropped_duplicate_rows"] != 0:
        print("  [FAIL] la limpieza no es idempotente")
        return 1
    print("  [OK] idempotencia")
    print("SELFTEST OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Limpieza reproducible de CSV (muestra de trabajo v1, zero-dependency)."
    )
    parser.add_argument("--in", dest="in_path", help="CSV de entrada (UTF-8)")
    parser.add_argument("--out", dest="out_path", help="CSV limpio de salida")
    parser.add_argument("--report", dest="report_path", default=None, help="ruta opcional del informe JSON")
    parser.add_argument("--selftest", action="store_true", help="ejecuta el auto-test interno")
    parser.add_argument("--version", action="store_true", help="muestra la version")
    args = parser.parse_args(argv)

    if args.version:
        print(f"clean_csv.py {__version__}")
        return 0
    if args.selftest:
        return selftest()
    if not args.in_path or not args.out_path:
        parser.error("se requieren --in y --out (o use --selftest)")
    report = run(args.in_path, args.out_path, args.report_path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
