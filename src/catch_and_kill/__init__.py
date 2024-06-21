#! /usr/bin/python3

import re
from enum import Enum
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


class AssayType(str, Enum):
    scrnaseq = "scrnaseq"
    scatacseq = "scatacseq"


catch_and_kill = typer.Typer(no_args_is_help=True)


@catch_and_kill.command(name="version", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def version_callback(value: Annotated[bool, typer.Option()] = True) -> None:  # FBT001
    """Prints the version of the package."""
    if value:
        rprint(f"[yellow]catch_and_kill[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()


@catch_and_kill.command()
def find_and_rename(
    count_folder: Annotated[
        Path, typer.Option("--counts", help="Parent directory containing sample cellranger output subdirectories")
    ],
    sample_prefix: Annotated[str, typer.Option("--prefix", help="Prefix common among sample names.")],
    sample_number_pattern: Annotated[
        str,
        typer.Option(
            "-p", "--pattern", help="Regular expression to match the sample name/numbers after the sample_prefix"
        ),
    ] = r"([0-9]{2})",
    output_folder: Annotated[
        Optional[Path], typer.Option("--output", help="Path to where files should be moved")
    ] = None,
    assay_type: Annotated[
        AssayType, typer.Option("--type", "-a", help="Type of assay performed, either scRNAseq or scATACseq.")
    ] = AssayType.scrnaseq,
    dry_run: Annotated[
        bool, typer.Option("--dry_run", "-d", help="Do not actually rename files but show what will be renamed")
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version number.",
        ),
    ] = False,
):
    """Find all of the web_summary files created by cellranger count/multi or cellranger-atac count that are present
    in sample subdirectories organized under a single parent and then more and rename the files
    """
    if output_folder is None:
        output_folder = Path.cwd()

    # allow explicit assay type argument because maybe the guess below will get it wrong?
    if assay_type == AssayType.scrnaseq:
        samples = [
            _
            for _ in count_folder.glob(f"{sample_prefix}*/outs/per_sample_outs/{sample_prefix}*/web_summary.html")
            if _.is_file()
        ]
    elif assay_type == AssayType.scatacseq:
        samples = [_ for _ in count_folder.glob(f"{sample_prefix}*/outs/web_summary.html") if _.is_file()]
    else:
        # nothing specified? let's guess!
        samples = [
            _
            for _ in count_folder.glob(f"{sample_prefix}*/outs/per_sample_outs/{sample_prefix}*/web_summary.html")
            if _.is_file()
        ] or [_ for _ in count_folder.glob(f"{sample_prefix}*/outs/web_summary.html") if _.is_file()]

    sample_numbers = [re.search(sample_prefix + sample_number_pattern, str(_))[1] for _ in samples]

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
    """Find the 'metrics_summary.csv' files for the output from cellranger-count and -multi for multiple samples that
    are organized under a single directory.
    """
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
    access_folder: Annotated[
        Path,
        typer.Argument(help="Path to the parent folder under which the scATAC-seq count folder for each sample are"),
    ],
    output: Annotated[Path, typer.Argument(help="Path to where the compiled report should be written")],
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Print version number.",
        ),
    ] = False,
):
    """Find the 'summary.csv' files for the output from cellranger-atac for multiple samples that are organized under
    a single directory.
    """
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
