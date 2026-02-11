"""Command-line interface for pykabu-calendar."""

from __future__ import annotations

import sys
from pathlib import Path

import click

import pykabu_calendar as cal


@click.group()
@click.version_option(version=cal.__version__, prog_name="pykabu-calendar")
def main():
    """Japanese earnings calendar aggregator."""


@main.command()
@click.argument("date")
@click.option("--no-ir", is_flag=True, help="Disable IR discovery.")
@click.option("--ir-eager", is_flag=True, help="Bypass IR cache, re-discover.")
@click.option("--no-infer", is_flag=True, help="Disable historical inference.")
@click.option("--sources", default=None, help="Comma-separated source list.")
@click.option(
    "-o", "--output", "output_path", default=None, type=click.Path(),
    help="Export to file (format from extension: .csv, .parquet, .db).",
)
@click.option(
    "-f", "--format", "fmt", default="table",
    type=click.Choice(["table", "csv", "json"]),
    help="Stdout format.",
)
def calendar(date, no_ir, ir_eager, no_infer, sources, output_path, fmt):
    """Get earnings calendar for DATE (YYYY-MM-DD)."""
    try:
        source_list = [s.strip() for s in sources.split(",")] if sources else None
        df = cal.get_calendar(
            date,
            sources=source_list,
            include_ir=not no_ir,
            ir_eager=ir_eager,
            infer_from_history=not no_infer,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if output_path:
        _export(df, output_path)
        click.echo(f"Exported {len(df)} rows to {output_path}")
        return

    if fmt == "csv":
        click.echo(df.to_csv(index=False))
    elif fmt == "json":
        click.echo(df.to_json(orient="records", date_format="iso", force_ascii=False))
    else:
        click.echo(df.to_string(index=False))


@main.command()
def check():
    """Health check all data sources."""
    try:
        results = cal.check_sources()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    for r in results:
        status = "ok" if r["ok"] else "FAIL"
        rows = r.get("rows", "?")
        line = f"  {r['name']:<15} {status:<6} rows={rows}"
        if not r["ok"] and r.get("error"):
            line += f"  error={r['error']}"
        click.echo(line)


@main.command()
@click.argument("code")
@click.option("--ir", "include_ir", is_flag=True, help="Include IR discovery.")
@click.option("--history", "n_history", default=8, show_default=True, help="Past earnings to show.")
def lookup(code, include_ir, n_history):
    """Look up earnings info for a single stock CODE."""
    try:
        past = cal.get_past_earnings(code, n_recent=n_history)
        inferred_dt, confidence, _ = cal.infer_datetime(code, "2099-01-01", past_datetimes=past)

        click.echo(f"Stock: {code}")
        click.echo(f"Inferred time: {inferred_dt} (confidence: {confidence})")
        if past:
            click.echo(f"Past announcements ({len(past)}):")
            for dt in past:
                click.echo(f"  {dt}")
        else:
            click.echo("No past announcements found.")

        if include_ir:
            page_info = cal.discover_ir_page(code)
            if page_info:
                click.echo(f"IR page: {page_info.url}")
                click.echo(f"  type: {page_info.page_type}, via: {page_info.discovered_via}")
            else:
                click.echo("IR page: not found")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def config():
    """Show current configuration."""
    settings = cal.get_settings()
    for field_name in sorted(settings.__dataclass_fields__):
        click.echo(f"  {field_name}: {getattr(settings, field_name)}")


def _export(df, path: str):
    """Export DataFrame to file, format detected from extension."""
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        cal.export_to_csv(df, path)
    elif ext in (".parquet", ".pq"):
        cal.export_to_parquet(df, path)
    elif ext in (".db", ".sqlite"):
        cal.export_to_sqlite(df, path)
    else:
        raise click.BadParameter(
            f"Unknown file extension '{ext}'. Use .csv, .parquet, or .db."
        )
