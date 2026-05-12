from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "payment_reconciliation_demo.duckdb"


def csv_path(relative_path: str) -> str:
    return (ROOT / relative_path).as_posix()


def execute_sql_files(connection: duckdb.DuckDBPyConnection) -> None:
    for sql_file in [
        "sql/01_raw_to_parsed.sql",
        "sql/02_key_generation.sql",
        "sql/03_reconciliation_logic.sql",
        "sql/04_reporting_views.sql",
        "sql/05_bi_views.sql",
    ]:
        connection.execute((ROOT / sql_file).read_text(encoding="utf-8"))


def build_database(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            output_path.unlink()
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot overwrite {output_path} because the file is in use. "
                "Close any open DuckDB/Streamlit session or choose a different --output path."
            ) from exc

    wal_path = output_path.with_suffix(output_path.suffix + ".wal")
    if wal_path.exists():
        wal_path.unlink()

    connection = duckdb.connect(database=output_path.as_posix())
    try:
        connection.execute("set preserve_insertion_order=false;")
        connection.execute("set threads=1;")
        connection.execute(
            f"""
            create table raw_payment_batches as
            select * from read_csv_auto('{csv_path("sample_data/payment_batches_sample.csv")}', header=true);

            create table raw_receipts as
            select * from read_csv_auto('{csv_path("sample_data/receipts_sample.csv")}', header=true);

            create table raw_gateway_reference_mapping as
            select * from read_csv_auto('{csv_path("sample_data/gateway_reference_mapping_sample.csv")}', header=true);
            """
        )

        execute_sql_files(connection)

        summary = connection.sql(
            """
            select object_name, row_count
            from reconciliation_runtime_summary
            order by object_name
            """
        ).fetchall()
    finally:
        connection.close()

    print(f"Built DuckDB demo database: {output_path}")
    for object_name, row_count in summary:
        print(f"- {object_name}: {row_count:,} rows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local DuckDB database for the sanitized reconciliation runtime demo."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output .duckdb path. Defaults to {DEFAULT_OUTPUT.name}.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_database(args.output.expanduser().resolve())


if __name__ == "__main__":
    main()
