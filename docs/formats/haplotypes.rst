.. _formats-haplotypes:


Haplotypes
==========

This document describes our custom file format specification for haplotypes: the ``.hap`` file.

This is a tab-separated file composed of different types of lines. The first field of each line is a single, uppercase character denoting the type of line. The following line types are supported.

.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Type
     - Description
   * - #
     - Comment
   * - H
     - Haplotype
   * - V
     - Variant

Each line type (besides #) has a set of mandatory fields described below. Additional "extra" fields can be appended to these to customize the file.

``#`` Comment line
~~~~~~~~~~~~~~~~~~
Comment lines begin with ``#`` and are ignored. Consecutive comment lines that appear at the beginning of the file are treated as part of the header.

Extra fields must be declared in the header. The declaration must be a tab-separated line containing the following fields:

1. Line type (ex: ``H`` or ``V``)
2. Name
3. Python format string (ex: 'd' for int, 's' for string, or '.3f' for a float with 3 decimals)
4. Description

Note that the first field must follow the ``#`` symbol immediately (ex: ``#H`` or ``#V``).


``H`` Haplotype
~~~~~~~~~~~~~~~
Haplotypes contain the following attributes:

.. list-table::
   :widths: 25 25 25 50
   :header-rows: 1

   * - Column
     - Field
     - Type
     - Description
   * - 1
     - Chromosome
     - string
     - The contig that this haplotype belongs on
   * - 2
     - Start Position
     - int
     - The start position of this haplotype on this contig
   * - 3
     - End Position
     - int
     - The end position of this haplotype on this contig
   * - 4
     - Haplotype ID
     - string
     - Uniquely identifies a haplotype

``V`` Variant
~~~~~~~~~~~~~
Each variant line belongs to a particular haplotype. These lines contain the following attributes:

.. list-table::
   :widths: 25 25 25 50
   :header-rows: 1

   * - Column
     - Field
     - Type
     - Description
   * - 1
     - Haplotype ID
     - string
     - Identifies the haplotype to which this variant belongs
   * - 2
     - Start Position
     - int
     - The start position of this variant on its contig
   * - 3
     - End Position
     - int
     - The end position of this variant on its contig

       Usually the same as the Start Position
   * - 4
     - Variant ID
     - string
     - The unique ID for this variant, as defined in the genotypes file
   * - 5
     - Allele
     - string
     - The allele of this variant within the haplotype

Examples
~~~~~~~~
You can find an example of a ``.hap`` file without any extra fields in `tests/data/basic.hap <https://github.com/gymrek-lab/haptools/blob/main/tests/data/basic.hap>`_:

.. include:: ../../tests/data/basic.hap
   :literal:

You can find an example with extra fields added within `tests/data/simphenotype.hap <https://github.com/gymrek-lab/haptools/blob/main/tests/data/simphenotype.hap>`_:

.. include:: ../../tests/data/simphenotype.hap
   :literal:


Compressing and indexing
~~~~~~~~~~~~~~~~~~~~~~~~
We encourage you to bgzip compress and/or index your ``.hap`` file whenever possible. This will reduce both disk usage and the time required to parse the file.

.. code-block:: bash

  sort -k1,4 -o file.hap file.hap
  bgzip file.hap
  tabix -s 2 -b 3 -e 4 file.hap.gz

In order to properly index the file, the IDs in the haplotype lines must be different from their chromosomes. In addition, you must sort on the first field (ie the line type symbol) in addition to the latter three.

Extra fields
~~~~~~~~~~~~
Additional fields can be appended to the ends of the haplotype and variant lines as long as they are declared in the header.

haptools extras
---------------
The following extra fields should be declared for your ``.hap`` file to be compatible with ``simphenotype``.

.. code-block::

  #H	ancestry	s	Local ancestry
  #H	beta	.2f	Effect size in linear model

..
  _TODO: figure out how to tab this code block so that the tabs get copied when someone copies from it


``H`` Haplotype
+++++++++++++++

.. list-table::
   :widths: 25 25 25 50
   :header-rows: 1

   * - Column
     - Field
     - Type
     - Description
   * - 5
     - Local Ancestry
     - string
     - A population code denoting this haplotype's ancestral origins
   * - 6
     - Effect Size
     - float
     - The effect size of this haplotype; for use in ``simphenotype``

``V`` Variant
+++++++++++++
No extra fields are required here.
