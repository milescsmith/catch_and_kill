#! /usr/bin/python3

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Optional

import polars as pl
import typer
from rich import print as rprint
from tqdm.auto import tqdm
from tqdm.contrib import tenumerate

# from rich.console import Console

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

catch_and_kill = typer.Typer(no_args_is_help=True)


@catch_and_kill.command(name="version", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def version_callback(value: Annotated[bool, typer.Option()] = True) -> None:  # FBT001
    """Prints the version of the package."""
    if value:
        rprint(f"[yellow]catch_and_kill[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()


@catch_and_kill.command()
def find_and_rename(
    count_folder: Annotated[Path, typer.Option("--counts")],
    sample_prefix: Annotated[str, typer.Option("--prefix")],
    output_folder: Annotated[Optional[Path], typer.Option("--output")] = None,
    dry_run: Annotated[bool, typer.Option("--dry_run", "-d")] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version number.",
        ),
    ] = False,
):
    if output_folder is None:
        output_folder = Path.cwd()

    samples = [
        _
        for _ in count_folder.glob(f"{sample_prefix}*/outs/per_sample_outs/{sample_prefix}*/web_summary.html")
        if _.is_file()
    ]

    sample_numbers = [re.search(sample_prefix + r"([0-9]{2})", str(_)).group(1) for _ in samples]

    for i, summary_file in tenumerate(samples):
        rprint(
            f"found [bold red]{summary_file.absolute()}[/bold red], moving to [bold green]{output_folder}/{sample_prefix}{sample_numbers[i]}_web_summary.html[/bold green]"
        )
        if not dry_run:
            summary_file.rename(f"{output_folder}/{sample_prefix}{sample_numbers[i]}_web_summary.html")


@catch_and_kill.command(name="count-metrics")
def to_me_my_count_metrics(
    count_folder: Annotated[Path, typer.Argument],
    output: Annotated[Path, typer.Argument],
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version number.",
        ),
    ] = False,
):
    sample_names = sorted(
        [
            _.name
            for _ in count_folder.iterdir()
            if _.is_dir()
            and count_folder.joinpath(_.name, "outs", "per_sample_outs", _.name, "metrics_summary.csv").exists()
        ]
    )

    metrics = [
        pl.read_csv(count_folder.joinpath(i, "outs", "per_sample_outs", i, "metrics_summary.csv"))
        .rename({"Metric Value": i})
        .drop("Group Name")
        for i in tqdm(sample_names)
        if count_folder.joinpath(i, "outs", "per_sample_outs", i, "metrics_summary.csv").exists()
    ]

    all_metrics = metrics[0]
    for i, _ in enumerate(metrics[1:]):
        all_metrics = all_metrics.with_columns(metrics[i][:, -1])

    all_metrics.write_csv(output)


@catch_and_kill.command(name="atac-metrics")
def to_me_my_accessability_metrics(
    access_folder: Annotated[Path, typer.Argument],
    output: Annotated[Path, typer.Argument],
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version number.",
        ),
    ] = False,
):
    sample_names = sorted(
        [
            _.name
            for _ in access_folder.iterdir()
            if _.is_dir() and access_folder.joinpath(_.name, "outs", "summary.csv").exists()
        ]
    )

    metrics = [
        pl.read_csv(access_folder.joinpath(i, "outs", "summary.csv"), has_header=False).transpose()
        for i in tqdm(sample_names)
        if access_folder.joinpath(i, "outs", "summary.csv").exists()
    ]

    all_metrics = metrics[0]
    for i, _ in enumerate(metrics[1:]):
        all_metrics = all_metrics.hstack([metrics[i][:, 1].alias(metrics[i][0, 1])])

    all_metrics.write_csv(output)
