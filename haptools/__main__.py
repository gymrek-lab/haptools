#!/usr/bin/env python

from __future__ import annotations
import sys
import time
import click
from pathlib import Path

# AVOID IMPORTING ANYTHING HERE
# any imports we put here will make it slower to use the command line client
# a basic "haptools --help" should be quick and require very few imports, for example

################### Haptools ##################
@click.group()
@click.version_option()
def main():
    """
    haptools: A toolkit for simulating and analyzing genotypes and 
    phenotypes while taking into account haplotype information
    """
    pass

############ Haptools karyogram ###############
@main.command()
@click.option('--bp', help="Path to .bp file with breakpoints", \
    type=str, required=True)
@click.option('--sample', help="Sample ID to plot", \
    type=str, required=True)
@click.option('--out', help="Name of output file", \
    type=str, required=True)
@click.option('--title', help="Optional plot title", \
    type=str, required=False)
@click.option('--centromeres', help="Optional file with telomere/centromere cM positions", \
    type=str, required=False)
@click.option('--colors', help="Optional color dictionary. Format is e.g. 'YRI:blue,CEU:green'", \
    type=str, required=False)
def karyogram(bp, sample, out, title, centromeres, colors):
    """
    Visualize a karyogram of local ancestry tracks
    
    Example:

    \b
    haptools karyogram --bp tests/data/5gen.bp --sample Sample_1 \\
       --out test.png --centromeres tests/data/centromeres_hg19.txt \\
       --colors 'CEU:blue,YRI:red'
    """
    from .karyogram import PlotKaryogram
    if colors is not None:
        colors = dict([item.split(":") for item in colors.split(",")])
    PlotKaryogram(bp, sample, out, \
        centromeres_file=centromeres, title=title, colors=colors)

############ Haptools simgenotype ###############
@main.command()
@click.option('--model', help="Admixture model in .dat format. See docs for info.", \
    type=str, required=True)
@click.option('--mapdir', help="Directory containing files with chr\{1-22,X\} and ending in .map in the file name with genetic map coords.", \
    required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('--out', help="Prefix to name output files.", \
    type=str, required=True)
@click.option('--chroms', help='Sorted and comma delimited list of chromosomes to simulate. ex: 1,2,3,5,6,21,X', \
    type=str, default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,X", required=True)
@click.option('--seed', help="Random seed. Set to make simulations reproducible", \
    type=int, required=False, default=None)
@click.option('--popsize', help="Number of samples to simulate each generation", \
    type=int, required=False, default=10000, hidden=True)
@click.option('--invcf', help="VCF file used as reference for creation of simulated samples respective genotypes.", required=True)
@click.option('--sample_info', help="File that maps samples from the reference VCF (--invcf) to population codes " \
              "describing the populations in the header of the model file.", required=True)
@click.option('--only_breakpoint', help="Flag used to determine whether to only output breakpoints or continue to simulate a vcf file.", \
    is_flag=True, required=False, hidden=True)
@click.option('--verbose', help="Output time metrics for each section, breakpoint simulation, vcf creation, and total exection.", \
     is_flag=True, required=False, hidden=True)
def simgenotype(invcf, sample_info, model, mapdir, out, popsize, seed, chroms, only_breakpoint, verbose):
    """
    Simulate admixed genomes under a pre-defined model.

    Example:

    \b
    haptools simgenotype \ 
      --model ./tests/data/outvcf_gen.dat \ 
      --mapdir ./tests/data/map/ \ 
      --chroms 1,2 \ 
      --invcf ./tests/data/outvcf_test.vcf \ 
      --sample_info ./tests/data/outvcf_info.tab \ 
      --out ./tests/data/example_simgenotype
    """
    from .sim_genotype import simulate_gt, write_breakpoints, output_vcf, validate_params
    start = time.time()

    chroms = chroms.split(',')
    validate_params(model, mapdir, chroms, popsize, invcf, sample_info, only_breakpoint)
    samples, breakpoints = simulate_gt(model, mapdir, chroms, popsize, seed)
    breakpoints = write_breakpoints(samples, breakpoints, out)
    bp_end = time.time()

    vcf_start = time.time()
    if not only_breakpoint:
        output_vcf(breakpoints, model, invcf, sample_info, out)
    end = time.time()

    if verbose:
        print(f"Time elapsed for breakpoint simulation: {bp_end - start}")
        print(f"Time elapse for creating vcf: {end - vcf_start}")
        print(f"Time elapsed for simgenotype execution: {end - start}")

############ Haptools simphenotype ###############
@main.command()
@click.argument("genotypes", type=click.Path(exists=True, path_type=Path))
@click.argument("haplotypes", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-r",
    "--replications",
    type=click.IntRange(min=1),
    default=1,
    show_default=True,
    help="Number of rounds of simulation to perform",
)
@click.option(
    "-h",
    "--heritability",
    type=click.FloatRange(min=0, max=1),
    default=None,
    show_default=True,
    help="Trait heritability",
)
@click.option(
    "-p",
    "--prevalence",
    type=click.FloatRange(min=0, max=1, min_open=False, max_open=True),
    show_default="quantitative trait",
    help="Disease prevalence if simulating a case-control trait"
)
@click.option(
    "--region",
    type=str,
    default=None,
    show_default="all haplotypes",
    help=(
        "The region from which to extract haplotypes; ex: 'chr1:1234-34566' or 'chr7'."
        "\nFor this to work, the VCF and .hap file must be indexed and the seqname "
        "provided must correspond with one in the files"
    )
)
@click.option(
    "-s",
    "--sample",
    "samples",
    type=str,
    multiple=True,
    show_default="all samples",
    help=(
        "A list of the samples to subset from the genotypes file (ex: '-s sample1 -s"
        " sample2')"
    ),
)
@click.option(
    "-S",
    "--samples-file",
    type=click.File("r"),
    show_default="all samples",
    help=(
        "A single column txt file containing a list of the samples (one per line) to"
        " subset from the genotypes file"
    ),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("/dev/stdout"),
    show_default="stdout",
    help="A TSV file containing simulated phenotypes",
)
@click.option(
    "-v",
    "--verbosity",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]),
    default="ERROR",
    show_default="only errors",
    help="The level of verbosity desired",
)
def simphenotype(
    genotypes: Path,
    haplotypes: Path,
    replications: int = 1,
    heritability: float = None,
    prevalence: float = None,
    region: str = None,
    samples: tuple[str] = tuple(),
    samples_file: Path = None,
    chunk_size: int = None,
    output: Path = Path("-"),
    verbosity: str = 'ERROR',
):
    """
    Haplotype-aware phenotype simulation. Create a set of simulated phenotypes from a
    set of haplotypes.

    GENOTYPES must be formatted as a VCF and HAPLOTYPES must be formatted according
    to the .hap format spec

    \f
    Examples
    --------
    >>> haptools simphenotype tests/data/example.vcf.gz tests/data/example.hap.gz > simulated.pheno

    Parameters
    ----------
    genotypes : Path
        The path to the genotypes in VCF format
    haplotypes : Path
        The path to the haplotypes in a .hap file
    replications : int, optional
        The number of rounds of simulation to perform
    heritability : int, optional
        The heritability of the simulated trait; must be a float between 0 and 1

        If not provided, it will be computed from the sum of the squared effect sizes.
    prevalence : int, optional
        The prevalence of the disease if the trait should be simulated as case/control;
        must be a float between 0 and 1

        If not provided, a quantitative trait will be simulated, instead
    region : str, optional
        The region from which to extract haplotypes; ex: 'chr1:1234-34566' or 'chr7'

        For this to work, the VCF and .hap file must be indexed and the seqname must
        match!

        Defaults to loading all haplotypes
    sample : tuple[str], optional
        A subset of the samples from which to extract genotypes

        Defaults to loading genotypes from all samples
    samples_file : Path, optional
        A single column txt file containing a list of the samples (one per line) to
        subset from the genotypes file
    chunk_size: int, optional
        The max number of variants to fetch from the PGEN file at any given time

        If this value is provided, variants from the PGEN file will be loaded in
        chunks so as to use less memory. This argument is ignored if the genotypes are
        not in PGEN format.
    output : Path, optional
        The location to which to write the simulated phenotypes
    verbosity : str, optional
        The level of verbosity desired in messages written to stderr
    """
    import logging

    from .sim_phenotype import simulate_pt

    log = logging.getLogger("run")
    logging.basicConfig(
        format="[%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
        level=verbosity,
    )
    # handle samples
    if samples and samples_file:
        raise click.UsageError(
            "You may only use one of --sample or --samples-file but not both."
        )
    if samples_file:
        with samples_file as samps_file:
            samples = samps_file.read().splitlines()
    elif samples:
        # needs to be converted from tuple to list
        samples = list(samples)
    else:
        samples = None

    # Run simulation
    simulate_pt(
        genotypes, haplotypes, replications, heritability, prevalence, region, samples,
        chunk_size, output, log
    )

@main.command(short_help="Transform a genotypes matrix via a set of haplotypes")
@click.argument("genotypes", type=click.Path(exists=True, path_type=Path))
@click.argument("haplotypes", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--region",
    type=str,
    default=None,
    show_default="all haplotypes",
    help=(
        "The region from which to extract haplotypes; ex: 'chr1:1234-34566' or 'chr7'."
        "\nFor this to work, the VCF and .hap file must be indexed and the seqname "
        "provided must correspond with one in the files"
    )
)
@click.option(
    "-s",
    "--sample",
    "samples",
    type=str,
    multiple=True,
    show_default="all samples",
    help=(
        "A list of the samples to subset from the genotypes file (ex: '-s sample1 -s"
        " sample2')"
    ),
)
@click.option(
    "-S",
    "--samples-file",
    type=click.File("r"),
    show_default="all samples",
    help=(
        "A single column txt file containing a list of the samples (one per line) to"
        " subset from the genotypes file"
    ),
)
@click.option(
    "-h",
    "--haplotype-ids",
    type=str,
    multiple=True,
    show_default="all haplotypes",
    help=(
        "A list of the haplotype IDs to use from the .hap file (ex: '-h H1 -h H2')."
        "\nFor this to work, the .hap file must be indexed"
    ),
)
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=None,
    show_default="all variants",
    help="If using a PGEN file, read genotypes in chunks of X variants; reduces memory",
)
@click.option(
    "--discard-missing",
    is_flag=True,
    show_default=True,
    default=False,
    help="Ignore any samples that are missing genotypes for the required variants",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("-"),
    show_default="stdout",
    help="A VCF file containing haplotype 'genotypes'",
)
@click.option(
    "-v",
    "--verbosity",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]),
    default="ERROR",
    show_default="only errors",
    help="The level of verbosity desired",
)
def transform(
    genotypes: Path,
    haplotypes: Path,
    region: str = None,
    samples: tuple[str] = tuple(),
    samples_file: Path = None,
    haplotype_ids: tuple[str] = tuple(),
    chunk_size: int = None,
    discard_missing: bool = False,
    output: Path = Path("-"),
    verbosity: str = 'CRITICAL',
):
    """
    Creates a VCF composed of haplotypes

    GENOTYPES must be formatted as a VCF or PGEN and HAPLOTYPES must be formatted
    according to the .hap format spec

    \f
    Examples
    --------
    >>> haptools transform tests/data/example.vcf.gz tests/data/example.hap.gz > example_haps.vcf

    Parameters
    ----------
    genotypes : Path
        The path to the genotypes
    haplotypes : Path
        The path to the haplotypes in a .hap file
    region : str, optional
        The region from which to extract haplotypes; ex: 'chr1:1234-34566' or 'chr7'

        For this to work, the VCF and .hap file must be indexed and the seqname must
        match!

        Defaults to loading all haplotypes
    sample : tuple[str], optional
        A subset of the samples from which to extract genotypes

        Defaults to loading genotypes from all samples
    samples_file : Path, optional
        A single column txt file containing a list of the samples (one per line) to
        subset from the genotypes file
    haplotype_ids: tuple[str], optional
        A list of haplotype IDs to obtain from the .hap file. All others are ignored.

        If not provided, all haplotypes will be used.
    chunk_size: int, optional
        The max number of variants to fetch from the PGEN file at any given time

        If this value is provided, variants from the PGEN file will be loaded in
        chunks so as to use less memory. This argument is ignored if the genotypes are
        not in PGEN format.
    discard_missing : bool, optional
        Discard any samples that are missing any of the required samples

        The default is simply to complain about it
    output : Path, optional
        The location to which to write output
    verbosity : str, optional
        The level of verbosity desired in messages written to stderr
    """
    import logging

    from .transform import transform_haps

    log = logging.getLogger("run")
    logging.basicConfig(
        format="[%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
        level=verbosity,
    )
    # handle samples
    if samples and samples_file:
        raise click.UsageError(
            "You may only use one of --sample or --samples-file but not both."
        )
    if samples_file:
        with samples_file as samps_file:
            samples = samps_file.read().splitlines()
    elif samples:
        # needs to be converted from tuple to list
        samples = list(samples)
    else:
        samples = None

    if haplotype_ids:
        haplotype_ids = set(haplotype_ids)
    else:
        haplotype_ids = None

    transform_haps(
        genotypes, haplotypes, region, samples, haplotype_ids, chunk_size,
        discard_missing, output, log
    )


if __name__ == "__main__":
    # run the CLI if someone tries 'python -m haptools' on the command line
    main(prog_name="haptools")
