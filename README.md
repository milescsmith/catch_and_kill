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

* `atac-metrics`
* `count-metrics`
* `find-and-rename`
* `version`: Prints the version of the package.

## `atac-metrics`

**Usage**:

```console
$ atac-metrics [OPTIONS] ACCESS_FOLDER OUTPUT
```

**Arguments**:

* `ACCESS_FOLDER`: [required]
* `OUTPUT`: [required]

**Options**:

* `--version`: Print version number.
* `--help`: Show this message and exit.

## `count-metrics`

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

**Usage**:

```console
$ find-and-rename [OPTIONS]
```

**Options**:

* `--counts PATH`: [required]
* `--prefix TEXT`: [required]
* `--output PATH`
* `-d, --dry_run`
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
