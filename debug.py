from pathlib import Path

from catch_and_kill import find_and_rename

find_and_rename(
    count_folder=Path("/mnt/scratch/guth-aci/SMILE/data/counts"),
    sample_prefix="SMILE_",
    cellranger_version=10,
    assay_type="scrnaseq",
    dry_run=True,
)
