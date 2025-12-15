# catch_and_kill

Utility script to gather and merge the CellRanger metrics summary files from cellranger-atac count or 
cellranger-multi count

# CLI

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `atac-metrics`: Find the 'summary.csv' files for the...
* `count-metrics`: Find the 'metrics_summary.csv' files for...
* `find-and-rename`: Find all of the web_summary files created...
* `version`: Prints the version of the package.

## `atac-metrics`

Find the 'summary.csv' files for the output from cellranger-atac for multiple samples that are organized under
a single directory.

**Usage**:

```console
$ atac-metrics [OPTIONS] ACCESS_FOLDER OUTPUT
```

**Arguments**:

* `ACCESS_FOLDER`: Path to the parent folder under which the scATAC-seq count folder for each sample are  [required]
* `OUTPUT`: Path to where the compiled report should be written  [required]

**Options**:

* `--version`: Print version number.
* `--help`: Show this message and exit.

## `count-metrics`

Find the 'metrics_summary.csv' files for the output from cellranger-count and -multi for multiple samples that
are organized under a single directory.

**Usage**:

```console
$ count-metrics [OPTIONS] COUNT_FOLDER OUTPUT
```

**Arguments**:

* `COUNT_FOLDER`: [required]
* `OUTPUT`: [required]

**Options**:

* `--version`: Print version number.
* `--help`: Show this message and exit.

## `find-and-rename`

Find all of the web_summary/qc_report files created by cellranger count/multi or cellranger-atac count that are present
in sample subdirectories organized under a single parent and then more and rename the files

**Usage**:

```console
$ find-and-rename [OPTIONS]
```

**Options**:

* `--counts PATH`: Parent directory containing sample cellranger output subdirectories  [required]
* `--summary-name STR`: Name of the Cell Ranger summary file. In older Cell Ranger versions it is 'web_summary.html', in newer it is 'qc_report.html' [default: 'web_summary.html']
* `--prefix TEXT`: Prefix common among sample names.  [required]
* `-p, --pattern TEXT`: Regular expression to match the sample name/numbers after the sample_prefix  [default: ([0-9]{2})]
* `--output PATH`: Path to where files should be moved
* `-a, --type [scRNAseq|scATACseq]`: Type of assay performed, either scRNAseq or scATACseq.
* `-d, --dry_run`: Do not actually rename files but show what will be renamed
* `--version`: Print version number.
* `--help`: Show this message and exit.

## `version`

Prints the version of the package.

**Usage**:

```console
$ version [OPTIONS]
```

**Options**:

* `--value / --no-value`: [default: value]
* `--help`: Show this message and exit.
