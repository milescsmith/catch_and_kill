#! /usr/bin/python3
import re
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import msgspec
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
    cellranger_version: Annotated[
        int | None,
        typer.Option(
            "--cr_version",
            # "-c",
            help="What version of Cell Ranger produced this output? If not provided, will attempt to read it from the sample's '_versions' file",
        ),
    ] = None,
    output_folder: Annotated[Path | None, typer.Option("--output", help="Path to where files should be moved")] = None,
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
    """Find all of the web_summary/qc_report files created by cellranger count/multi or cellranger-atac count that are present
    in sample subdirectories organized under a single parent and then more and rename the files
    """
    if output_folder is None:
        output_folder = Path.cwd()

    # allow explicit assay type argument because maybe the guess below will get it wrong?

    sample_folders: list[Path] = [
        _ for _ in count_folder.glob(f"{sample_prefix}*") if (_.is_dir() and _.joinpath("outs/").exists())
    ]
    if len(sample_folders) == 0:
        msg = f"No valid Cell Ranger outputs were found at {count_folder!s}"
        raise FileNotFoundError(msg)

    if cellranger_version is None:
        versions_file = sample_folders[0].joinpath("_versions")
        if versions_file.exists():
            raw_version = msgspec.json.decode(versions_file.read_bytes())["pipelines"]
            cellranger_version = int(raw_version.split(".")[0])
            msg = f"The Cell Ranger version was not provided. Inferring that it is [bold skyblue]{raw_version}[/] from the files found."
            rprint(msg)
        else:
            msg = f"You did not pass the Cell Ranger version argument and the file used for guessing ({versions_file}) cannot be found"
            raise ValueError(msg)

    cellranger_version_where_changes_happened = 10
    match x := cellranger_version:
        case _ if x >= cellranger_version_where_changes_happened:
            run_report_name = "qc_report.html"
            report_location = f"{sample_prefix}*/outs"
        case _ if x < cellranger_version_where_changes_happened:
            run_report_name = "web_summary.html"
            report_location = f"{sample_prefix}*/outs/per_sample_outs/{sample_prefix}*"

    match assay_type:
        case AssayType.scrnaseq:
            samples = [_ for _ in count_folder.glob(f"{report_location}/{run_report_name}") if _.is_file()]
        case AssayType.scatacseq:
            samples = [_ for _ in count_folder.glob(f"{sample_prefix}*/outs/{run_report_name}") if _.is_file()]
        case _:
            # nothing specified? let's guess!
            samples = [
                _
                for _ in count_folder.glob(f"{sample_prefix}*/outs/per_sample_outs/{sample_prefix}*/{run_report_name}")
                if _.is_file()
            ] or [_ for _ in count_folder.glob(f"{sample_prefix}*/outs/{run_report_name}") if _.is_file()]

    sample_numbers = [x.group(1) for y in samples if (x := re.search(sample_prefix + sample_number_pattern, str(y)))]

    for i, summary_file in tenumerate(samples):
        rprint(
            f"found [bold red]{summary_file.absolute()}[/bold red], moving to [bold green]{output_folder}/{sample_prefix}{sample_numbers[i]}_{run_report_name}[/bold green]"
        )
        if not dry_run:
            summary_file.rename(f"{output_folder}/{sample_prefix}{sample_numbers[i]}_{run_report_name}")


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
