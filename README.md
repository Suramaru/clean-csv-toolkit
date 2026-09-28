# clean-csv-toolkit

Single-file, dependency-free CSV cleaning utility (Python 3.10+) with a deterministic self-test.

Small reproducible work sample: deterministic behavior, no third-party dependencies, no network access, no sensitive data.

## What it does

1. Normalizes headers to ASCII snake_case (`col_N` when empty) and deduplicates repeated headers.
2. Trims whitespace in every cell.
3. Drops fully empty rows.
4. Drops fully empty columns.
5. Removes exact duplicate rows (after trimming), keeping the first.
6. Emits a JSON report with before/after counters and headers.

## Usage

```bash
python clean_csv.py --in input.csv --out cleaned.csv --report report.json
python clean_csv.py --selftest
python clean_csv.py --version
```

## Limits

- Does not infer data types.
- UTF-8 input only.
- Not intended for sensitive personal data.

## License

MIT