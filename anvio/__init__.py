# -*- coding: utf-8

"""Lots of under-the-rug, operational garbage in here. Run. Run away.."""

import os
import sys
import copy
import pkg_resources


# Make sure the Python environment hasn't changed since the installation (happens more often than you'd think
# on systems working with multiple Python installations that are managed through modules):
try:
    if sys.version_info < (2, 7, 5):
        v =  '.'.join([str(x) for x in sys.version_info[0:3]])
        sys.stderr.write("Your active Python version is '%s'. Anything less than '2.7.5' will not do it for anvi'o :/\n" % v)
        sys.exit(-1)
except Exception:
    sys.stderr.write("(anvi'o failed to learn about your Python version, but it will pretend as if nothing happened)\n\n")


# a comprehensive arguments dictionary that provides easy access from various programs that interface anvi'o modules:
D = {
    'profile-db': (
            ['-p', '--profile-db'],
            {'metavar': "PROFILE_DB",
             'required': True,
             'help': "Anvi'o profile database"}
                ),
    'serialized-profile': (
            ['-d', '--serialized-profile'],
            {'metavar': "PROFILE",
             'help': "Serialized profile (PROFILE.cp). This file would be a result of a previous\
                      anvi'o profiling run. It is faster, and can be used to refine previously obtained results."}
                ),
    'samples-information-db': (
            ['-s', '--samples-information-db'],
            {'metavar': 'SAMPLES_DB',
             'help': "Samples information database generated by 'anvi-gen-samples-info-database'"}
                ),
    'contigs-db': (
            ['-c', '--contigs-db'],
            {'metavar': 'CONTIGS_DB',
             'required': True,
             'help': "Anvi'o contigs database generated by 'anvi-gen-contigs'"}
                ),
    'runinfo': (
            ['-r', '--runinfo'],
            {'metavar': 'RUNINFO_PATH',
             'required': True,
             'help': "Anvi'o runinfo file path."}
                ),
    'additional-view': (
            ['-V', '--additional-view'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "A TAB-delimited file for an additional view to be used in the interface. This\
                      file file should contain all split names, and values for each of them in all\
                      samples. Each column in this file must correspond to a sample name. Content\
                      of this file will be called 'user_vuew', which will be available as a new item\
                      in the 'views' combo box in the interface"}
                ),
    'fasta-file': (
            ['-f', '--fasta-file'],
            {'metavar': 'FASTA',
             'help': "A FASTA-formatted input file"}
                ),
    'samples-information': (
            ['-D', '--samples-information'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "A TAB-delimited file with information about samples in your dataset (which also correspond)\
                      to 'view layers'. Each row in this file must correspond to a sample name. Each column must\
                      contain a unique attribute. Please refer to the documentation to learn more about the \
                      structure and purpose of this file."}
                ),
    'samples-order': (
            ['-R', '--samples-order'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "A TAB-delimited file with three columns: 'attribute', 'basic', 'newick'. For each attribute,\
                      the order of samples must be defined either in the 'basic' form or via a 'newick'-formatted\
                      tree structurei that describes the organization of each sample. Anvi'o will look for a\
                      comma-separated list of sample names for the 'basic' form. Please refer to the online docs\
                      for more info. Also you shouldn't hesitate to try to find the right file format until you get\
                      it working. There are stringent checks on this file, and you will not break anything while trying!."}
                ),
    'split-length': (
            ['-L', '--split-length'],
            {'metavar': 'INT',
             'default': 20000,
             'type': int,
             'help': "Splitting very large contigs into multiple pieces improves the efficacy of the\
                      visualization step. The default value is (%(default)d). If you are not sure, we\
                      advise you to not go below 10,000. The lower you go, the more complicated the\
                      tree will be, and will take more time and computational resources to finish the\
                      analysis. Also this is not a case of 'the smaller the split size the more sensitive\
                      the results'. If you do not want your contigs to be split, you can either enter a very\
                      large integer, or '-1'."}
                ),
    'kmer-size': (
            ['-K', '--kmer-size'],
            {'metavar': 'INT',
             'default': 4,
             'type': int,
             'help': "K-mer size for k-mer frequency calculations. The default k-mer size for composition-based\
                      analyses is 4, historically. Although tetra-nucleotide frequencies seem to offer the\
                      the sweet spot of sensitivity, information density, and manageable number of dimensions\
                      for clustering approaches, you are welcome to experiment (but maybe you should leave\
                      it as is for your first set of analyses)."}
                ),
    'skip-gene-calling': (
            ['--skip-gene-calling'],
            {'default': False,
             'action': 'store_true',
             'help': "By default, generating an anvi'o contigs database includes the identification of open reading\
                      frames in contigs by running a bacterial gene caller. Declaring this flag will by-pass that\
                      process. If you prefer, you can later import your own gene calling results into the database."}
                ),
    'contigs-fasta': (
            ['-f', '--contigs-fasta'],
            {'metavar': 'FASTA',
             'required': True,
             'help': "The FASTA file that contains reference sequences you mapped your samples against. This\
                      could be a reference genome, or contigs from your assembler. Contig names in this file\
                      must match to those in other input files. If there is a problem anvi'o will gracefully\
                      complain about it."}
                ),
    'view-data': (
            ['-d', '--view-data'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "A TAB-delimited file for view data"}
                ),
    'tree': (
            ['-t', '--tree'],
            {'metavar': 'NEWICK',
             'help': "NEWICK formatted tree structure"}
                ),
    'additional-layers': (
            ['-A', '--additional-layers'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "A TAB-delimited file for additional layers for splits. The first column of this file\
                      must be split names, and the remaining columns should be unique attributes.\
                      The file does not need to contain all split names, or values for each split in\
                      every column. Anvi'o will try to deal with missing data nicely. Each column in this\
                      file will be visualized as a new layer in the tree."}
                ),
    'view': (
            ['--view'],
            {'metavar': 'NAME',
             'help': "Start the interface with a pre-selected view. To see a list of available views,\
                      use --show-views flag."}
                ),
    'table': (
            ['--table'],
            {'metavar': 'TABLE_NAME',
             'help': "Table name to export."}
                ),
    'fields': (
            ['-f', '--fields'],
            {'metavar': 'FIELD(S)',
             'help': "Fields to report. USe --list-tables parameter with a table name to see available\
                      fields  You can list fields using this notation: --fields 'field_1, field_2, ... field_N'."}
                ),
    'list': (
            ['-l', '--list'],
            {'default': False,
             'action': 'store_true',
             'help': "Gives a list of tables in a database and quits. If a table is already declared\
                      this time it lists all the fields in a given table, in case you would to export\
                      only a specific list of fields from the table using --fields parameter."}
                ),
    'title': (
            ['--title'],
            {'metavar': 'NAME',
             'help': "Title for the interface. If you are working with a RUNINFO dict, the title\
                      will be determined based on information stored in that file. Regardless,\
                      you can override that value using this parameter. If you are not using a\
                      anvio RUNINFO dictionary, a meaningful title will appear in the interface\
                      only if you define one using this parameter."}
                ),
    'split-hmm-layers': (
            ['--split-hmm-layers'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared, this flag tells the interface to split every gene found in HMM\
                      searches that were performed against non-singlecopy gene HMM profiles into\
                      their own layer. Please see the documentation for details."}
                ),
    'hmm-sources': (
            ['--hmm-sources'],
            {'metavar': 'SOURCE NAME',
             'help': "Get sequences for a specific list of HMM sources. You can list one or more\
                      sources by separating them from each other with a comma character (i.e., \
                      '--hmm-sources source_1,source_2,source_3'). If you would like to see a list\
                      of available sources in the contigs database, run this program with\
                      '--list-available-hmm-sources' flag."}
                ),
    'list-available-hmm-sources': (
            ['-l', '--list-available-hmm-sources'],
            {'default': False,
             'action': 'store_true',
             'help': "List available HMM sources in the profile database and quit."}
                ),
    'search-terms': (
            ['--search-terms'],
            {'metavar': 'SEARCH_TERMS',
             'help': "Search terms. Multiple of them can be declared separated by comma."}
                ),
    'list-contigs': (
            ['--list-contigs'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared, the program will list contigs in the BAM file and exit gracefully\
                      without any further analysis."}
                ),
    'list-collections': (
            ['--list-collections'],
            {'default': False,
             'action': 'store_true',
             'help': "Show available collections and exit."}
                ),
    'show-views': (
            ['--show-views'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared, the program will show a list of available views, and exit."}
                ),
    'list-completeness-sources': (
            ['--list-completeness-sources'],
            {'default': False,
             'action': 'store_true',
             'help': "Show available sources and exit."}
                ),
    'completeness-source': (
            ['--completeness-source'],
            {'metavar': 'NAME',
             'help': "Single-copy gene source to use to estimate completeness."}
                ),
    'splits-of-interest': (
            ['--splits-of-interest'],
            {'metavar': 'FILE',
             'help': "A file with split names. There should be only one column in the file, and each line\
                      should correspond to a unique split name."}
                ),
    'contigs-of-interest': (
            ['--contigs-of-interest'],
            {'metavar': 'FILE',
             'help': "It is possible to analyze only a group of contigs from a given BAM file. If you provide\
                      a text file, in which every contig of interest is listed line by line, the profiler would\
                      focus only on those contigs in the BAM file and ignore the rest. This can be used for\
                      debugging purposes, or to focus on a particular group of contigs that were identified as\
                      relevant during the interactive analysis."}
                ),
    'bin-id': (
            ['-b', '--bin-id'],
            {'metavar': 'BIN_NAME',
             'help': "Bin name you are interested in."}
                ),
    'bin-ids-file': (
            ['-B', '--bin-ids-file'],
            {'metavar': 'FILE_PATH',
             'help': "Text file for bins (each line should be a unique bin id)."}
                ),
    'collection-id': (
            ['-C', '--collection-id'],
            {'metavar': 'COLLECTION_NAME',
             'help': "Collection ID you are interested in."}
                ),
    'num-positions-from-each-split': (
            ['--num-positions-from-each-split'],
            {'metavar': 'INT',
             'default': 2,
             'type': int,
             'help': "Each split may have one or more variable positions. What is the maximum number of positons\
                      to report from each split is described via this paramter. The default is %(default)d. Which\
                      means from every split, a maximum of %(default)d eligable SNP is going to be reported."}
             ),
    'min-scatter': (
            ['-m', '--min-scatter'],
            {'metavar': 'INT',
             'default': 1,
             'type': int,
             'help': "This one is tricky. If you have N samples in your dataset, a given variable position x in one\
                      of your splits can split your N samples into `t` groups based on the identity of the\
                      variation they harbor at position x. For instance, `t` would have been 1, if all samples had the same\
                      type of variation at position x (which would not be very interesting, because in this case\
                      position x would have zero contribution to a deeper understanding of how these samples differ\
                      based on variability. When `t` > 1, it would mean that identities at position x across samples\
                      do differ. But how much scattering occurs based on position x when t > 1? If t=2, how many\
                      samples ended in each group? Obviously, even distribution of samples across groups may tell\
                      us something different than uneven distribution of samples across groups. So, this parameter\
                      filters out any x if 'the number of samples in the second largest group' (=scatter) is less\
                      than -m. Here is an example: lets assume you have 7 samples. While 5 of those have AG, 2\
                      of them have TC at position x. This would mean scatter of x is 2. If you set -m to 2, this\
                      position would not be reported in your output matrix. The default value for -m is\
                      %(default)d, which means every x found in the database and survived previous filtering\
                      criteria will be reported. Naturally, -m can not be more than half of the number of samples.\
                      Please refer to the user documentation if this is confusing."}
                ),

    'min-coverage-in-each-sample': (
            ['--min-coverage-in-each-sample'],
            {'metavar': 'INT',
             'default': 0,
             'type': int,
             'help': "Minimum coverage of a given variable nucleotide position in all samples. If a nucleotide position\
                      is covered less than this value even in one sample, it will be removed from the analysis. Default\
                      is %(default)d."}
                ),
    'min-ratio-of-competings-nts': (
            ['-r', '--min-ratio'],
            {'metavar': 'FLOAT',
             'default': 0,
             'type': float,
             'help': "Minimum ratio of the competing nucleotides at a given position. Default is %(default)f."}
                ),
    'min-occurrence-of-variable-postiions': (
            ['-x', '--min-occurrence'],
            {'metavar': 'NUM_SAMPLES',
             'default': 1,
             'type': int,
             'help': "Minimum number of samples a nucleotide position should be reported as variable. Default is %(default)d.\
                      If you set it to 2, for instance, each eligable variable position will be expected to appear in at least\
                      two samples, which will reduce the impact of stochastic, or unintelligeable varaible positions."}
                ),
    'samples-of-interest': (
            ['--samples-of-interest'],
            {'metavar': 'FILE',
             'help': "A file with samples names. There should be only one column in the file, and each line\
                      should correspond to a unique sample name."}
                ),
    'quince-mode': (
            ['--quince-mode'],
            {'default': False,
             'action': 'store_true',
             'help': "The default behavior is to report base frequencies of nucleotide positions only if there\
                      is any variation reported during profiling (which by default uses some heuristics to minimize\
                      the impact of error-driven variation). So, if there are 10 samples, and a given position has been\
                      reported as a varaible site during profiling in only one of those samples, there will be no\
                      information will be stored in the database for the remaining 9. When this flag is\
                      used, we go back to each sample, and report base frequencies for each sample at this position\
                      even if they do not vary. It will take considerably longer to report when this flag is on, and the use\
                      of it will increase the file size dramatically, however it is inevitable for some statistical approaches\
                      (as well as for some beautiful visualizations)."}
                ),
    'transpose': (
            ['--transpose'],
            {'default': False,
             'action': 'store_true',
             'help': "Transpose the input matrix file before clustering."}
                ),
    'skip-check-names': (
            ['--skip-check-names'],
            {'default': False,
             'action': 'store_true',
             'help': "For debugging purposes. You should never really need it."}
                ),
    'experimental-org-input-dir': (
            ['-i', '--input-directory'],
            {'metavar': 'DIR_PATH',
             'type': str,
             'help': "Input directory where the input files addressed from the configuration\
                      file can be found (i.e., the profile database, if PROFILE.db::TABLE\
                      notation is used in the configuration file)."}
                ),
    'clustering-name': (
            ['-N', '--name'],
            {'metavar': 'NAME',
             'type': str,
             'help': "The name to use when storing the resulting clustering in the database.\
                      This name will appear in the interactive interface and other relevant\
                      interfaces. Please consider using a short and descriptive single-word\
                      (if you do not do that you will make anvi'o complain)."}
                ),
    'output-dir': (
            ['-o', '--output-dir'],
            {'metavar': 'DIR_PATH',
             'type': str,
             'help': "Directory path for output files"}
                ),
    'output-file': (
            ['-o', '--output-file'],
            {'metavar': 'FILE_PATH',
             'type': str,
             'help': "File path to store results."}
                ),
    'output-db-path': (
            ['-o', '--output-db-path'],
            {'metavar': 'DB_FILE_PATH',
             'type': str,
             'help': "Output file path for the new database."}
                ),
    'output-file-prefix': (
            ['-O', '--output-file-prefix'],
            {'metavar': 'FILENAME_PREFIX',
             'type': str,
             'help': "A prefix to be used while naming the output files (no file type\
                      extensions please; just a prefix)."}
                ),
    'dry-run': (
            ['--dry-run'],
            {'default': False,
             'action': 'store_true',
             'help': "Don't do anything real. Test everything, and stop right before wherever the developer\
                      said 'well, this is enough testing', and decided to print out results."}
                ),
    'verbose': (
            ['--verbose'],
            {'default': False,
             'action': 'store_true',
             'help': "Be verbose, print more messages whenever possible."}
                ),
    'debug': (
            ['--debug'],
            {'default': False,
             'action': 'store_true',
             'help': "Turn on debug messages whenever possible, and skip removing temporary files (this may\
                      cause lots and lots of output, so you may want to not use it if your intention is not\
                      debugging)."}
                ),
    'ip-address': (
            ['-I', '--ip-address'],
            {'metavar': 'IP_ADDR',
             'type': str,
             'default': '0.0.0.0',
             'help': "IP address for the HTTP server. The default ip address (%(default)s) should\
                      work just fine for most."}
                ),
    'port-number': (
            ['-P', '--port-number'],
            {'metavar': 'INT',
             'default': 8080,
             'type': int,
             'help': "Port number to use for communication; the default (%(default)d) should be OK\
                      for almost everyone."}
                ),
    'read-only': (
            ['--read-only'],
            {'default': False,
             'action': 'store_true',
             'help': "When the interactive interface is started with this flag, all 'database write'\
                      operations will be disabled."}
                ),
    'server-only': (
            ['--server-only'],
            {'default': False,
             'action': 'store_true',
             'help': "The default behavior is to start the local server, and fire up a browser that\
                      connects to the server. If you have other plans, and want to start the server\
                      without calling the browser, this is the flag you need."}
                ),
    'skip-store-in-db': (
            ['--skip-store-in-db'],
            {'default': False,
             'action': 'store_true',
             'help': "By default, analysis results are stored in the profile database. The use of\
                      this flag will let you skip that"}
                ),
    'source-identifier': (
            ['--source-identifier'],
            {'metavar': 'NAME',
             'default': 'UNKNOWN_SOURCE',
             'help': "The source identifier when results are stored in the profile database. The default id\
                      is '%(default)s'. If there is another entry for '%(default)s', it will most likely be\
                      over-written with new results. You can use specific names via this parameter to avoid\
                      that."}
                ),
    'min-e-value': (
            ['-e', '--min-e-value'],
            {'metavar': 'E-VALUE',
             'default': 1e-15,
             'type': float,
             'help': "Minimum significance score of an HMM find to be considered as a valid hit.\
                      Default is %(default)g."}
                ),
    'colors': (
            ['--colors'],
            {'metavar': 'TAB_DELIM_FILE',
             'help': "Colors for bins. There must be two TAB-delimited columns, where the first should be a\
             unique bin name, and the second should be a 7 character HTML color code (i.e., '#424242')."}
                ),
    'contigs-mode': (
            ['--contigs-mode'],
            {'default': False,
             'action': 'store_true',
             'help': "Use this flag if your binning was done on contigs instead of splits. Please refer\
                      to the documentation for help."}
                ),
    'sample-name': (
            ['-S', '--sample-name'],
            {'metavar': 'NAME',
             'help': "It is important to set a sample name (using only ASCII letters and digits\
                      and without spaces) that is unique (considering all others). If you do not\
                      provide one, anvi'o will try to make up one for you based on other information,\
                      although, you should never let the software to decide these things)."}
                ),
    'skip-hierarchical-clustering': (
            ['--skip-hierarchical-clustering'],
            {'default': False,
             'action': 'store_true',
             'help': "If you are not planning to use the interactive interface (or if you have other\
                      means to add a tree of contigs in the database) you may skip the clustering step\
                      and simply just merge multiple runs"}
                ),
    'cluster-contigs': (
            ['--cluster-contigs'],
            {'default': False,
             'action': 'store_true',
             'help': "Single profiles are rarely used for genome binning or visualization, and since\
                      clustering step increases the profiling runtime for no good reason, the default\
                      behavior is to not cluster contigs for individual runs. However, if you are\
                      planning to do binning on one sample, you must use this flag to tell anvio to\
                      run cluster configurations for single runs on your sample."}
                ),
    'skip-concoct-binning': (
            ['--skip-concoct-binning'],
            {'default': False,
             'action': 'store_true',
             'help': "Anvi'o uses CONCOCT (Alneberg et al.) by default for unsupervised genome binning\
                      for merged runs. CONCOCT results are stored in the profile database, which then\
                      can be used from within appropriate interfaces (i.e., anvi-interactive, anvi-summary,\
                      etc). Use this flag if you would like to skip this step"}
                ),
    'overwrite-output-destinations': (
            ['-W', '--overwrite-output-destinations'],
            {'default': False,
             'action': 'store_true',
             'help': "Overwrite if the output files and/or directories exist."}
                ),
    'report-variability-full': (
            ['--report-variability-full'],
            {'default': False,
             'action': 'store_true',
             'help': "One of the things anvi-profile does is to store information about variable\
                      nucleotide positions. Usually it does not report every variable position, since\
                      not every variable position is geniune variation. Say, if you have 1,000 coverage,\
                      and all nucleotides at that position are Ts and only one of them is a C, the\
                      confidence of that C being a real variation is quite low. anvio has a simple\
                      algorithm in place to reduce the impact of noise. However, using this flag\
                      you can diable it and ask profiler to report every single variation (which\
                      may result in very large output files and millions of reports, but you are the\
                      boss). Do not forget to take a look at '--min-coverage-for-variability' parameter"}
                ),
    'manual-mode': (
            ['--manual-mode'],
            {'default': False,
             'action': 'store_true',
             'help': "Using this flag, you can run the interactive interface in an ad hoc manner using\
                      input files you curated instead of standard output files generated by an anvi'o\
                      run. In the manual mode you will be asked to provide a profile database. In this\
                      mode a profile database is only used to store 'state' of the interactive interface\
                      so you can reload your visual settings when you re-analyze the same files again. If\
                      the profile database you provide does not exist, anvi'o will create an empty one for\
                      you."}
                ),

    'hmm-profile-dir': (
            ['-H', '--hmm-profile-dir'],
            {'metavar': 'PATH',
             'help': "If this is empty, anvi'o will perform the HMM search against the default collections that\
                      are on the system. If it is not, this parameter should be used to point to a directory\
                      that contains 4 files: (1) genes.hmm.gz, (2) genes.txt, (3) kind.txt, and (4)\
                      reference.txt. Please see the documentation for specifics of these files."}
                ),
    'min-contig-length': (
            ['-M', '--min-contig-length'],
            {'metavar': 'INT',
             'default': 5000,
             'type': int,
             'help': "Minimum length of contigs in a BAM file to analyze. The minimum length should be long enough\
                      for tetra-nucleotide frequency analysis to be meaningful. There is no way to define a golden\
                      number of minumum length that would be applicable to genomes found in all environments, but we\
                      chose the default to be %(default)d, and have been happy with it. You are welcome to experiment,\
                      but we advise to never go below 1,000. You also should remember that the lower you go, the more\
                      time it will take to analyze all contigs. You can use --list-contigs parameter to have an idea how\
                      many contigs would be discarded for a given M."}
                ),
    'min-mean-coverage': (
            ['-X', '--min-mean-coverage'],
            {'metavar': 'INT',
             'default': 0,
             'type': int,
             'help': "Minimum mean coverage for contigs to be kept in the analysis. The default value is %(default)d,\
                      which is for your best interest if you are going to profile muptiple BAM files which are then\
                      going to be merged for a cross-sectional or time series analysis. Do not change it if you are not\
                      sure this is what you want to do."}
                ),
    'min-coverage-for-variability': (
            ['-V', '--min-coverage-for-variability'],
            {'metavar': 'INT',
             'default': 10,
             'type': int,
             'help': "Minimum coverage of a nucleotide position to be subjected to SNP profiling. By default, anvio will\
                      not attempt to make sense of variation in a given nucleotide position if it is covered less than\
                      %(default)dX. You can change that minimum using this parameter."}
                ),
    'contigs-and-positions': (
            ['-P', '--contigs-and-positions'],
            {'metavar': 'TAB_DELIM_FILE',
             'required': True,
             'help': "This is the file where you list the contigs, and nucleotide positions you are interested in. This\
                      is supposed to be a TAB-delimited file with two columns. In each line, the first column should be\
                      the contig name, and the second column should be the comma-separated list of integers for nucleotide\
                      positions."}
                ),
    'state': (
            ['--state'],
            {'metavar': 'NAME',
             'help': "Automatically load previous saved state and draw tree. To see a list of available states,\
                      use --show-states flag."}
                ),
    'show-states': (
            ['--show-states'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared the program will print all available states and exit."}
                ),
    'skip-init-functions': (
            ['--skip-init-functions'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared, function calls for genes will not be initialized (therefore will be missing from all\
                      relevant interfaces or output files). The use of this flag may reduce the memory fingerprint and\
                      processing time for large datasets."}
                ),
    'quick-summary': (
            ['--quick-summary'],
            {'default': False,
             'action': 'store_true',
             'help': "When declared the summary output will be generated as quickly as possible, with minimum amount\
                      of essential information about bins."}
                ),

}

# two functions that works with the dictionary above.
def A(param_id):
    return D[param_id][0]

def K(param_id, params_dict = {}):
    kwargs = copy.deepcopy(D[param_id][1])
    for key in params_dict:
        kwargs[key] = params_dict[key]

    return kwargs


# The rest of this file is composed of code that responds to '-v' or '--version' calls from clients,
# and provides access to the database version numbers for all anvi'o modules.

import anvio.tables as t
from anvio.terminal import Run


run = Run()


def set_version():
    try:
        __version__ = pkg_resources.require("anvio")[0].version
    except:
        # maybe it is not installed but being run from the codebase dir?
        try:
            __version__ = open(os.path.normpath(os.path.dirname(os.path.abspath(__file__))) + '/../VERSION').read().strip()
        except:
            __version__ = 'unknown'

    return __version__, t.contigs_db_version, t.profile_db_version, t.samples_info_db_version, t.auxiliary_hdf5_db_version


def print_version():
    run.info("Anvi'o version", __version__, mc = 'green')
    run.info("Contigs DB version", __contigs__version__)
    run.info("Profile DB version", __profile__version__)
    run.info("Samples information DB version", __samples__version__)
    run.info("Auxiliary HDF5 DB version", __hdf5__version__)


__version__, __contigs__version__, __profile__version__, __samples__version__, __hdf5__version__ = set_version()


if '-v' in sys.argv or '--version' in sys.argv:
    print_version()
    sys.exit()
