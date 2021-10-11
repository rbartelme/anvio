# -*- coding: utf-8
# pylint: disable=line-too-long
""" Classes to define and work with anvi'o trnaseq workflows. """


import os
import anvio
import pandas as pd
import anvio.utils as u
import anvio.terminal as terminal
import anvio.workflows as w
import anvio.filesnpaths as filesnpaths

from anvio.errors import ConfigError
from anvio.workflows import WorkflowSuperClass
from anvio.workflows.metagenomics import MetagenomicsWorkflow


__author__ = "Developers of anvi'o (see AUTHORS.txt)"
__copyright__ = "Copyleft 2015-2020, the Meren Lab (http://merenlab.org/)"
__credits__ = []
__license__ = "GPL 3.0"
__version__ = anvio.__version__
__maintainer__ = "Matthew S. Schechter"
__email__ = "mschechter@uchicago.edu"


run = terminal.Run()

class ExternalEcoPhyloWorkflow(WorkflowSuperClass):

    def __init__(self, args=None, run=terminal.Run(), progress=terminal.Progress()):
        self.init_workflow_super_class(args, workflow_name='external_ecophylo')

        # Snakemake rules
        self.rules.extend(['anvi_run_hmms_hmmsearch',
                           'filter_hmm_hits_by_query_coverage',
                           'anvi_get_sequences_for_hmm_hits_SCGs',
                           'anvi_estimate_scg_taxonomy_for_SCGs',
                           'filter_for_scg_sequences_and_metadata',
                           'cat_ribo_proteins_to_one_fasta',
                           'anvi_script_reformat_fasta',
                           'cat_misc_data_to_one_file',
                           'join_renamed_fasta_with_misc_data',
                           'remove_redundant_sequences_mmseqs',
                           'align_muscle',
                           'trim_alignment',
                           'remove_sequences_with_X_percent_gaps',
                           'get_gap_count_distribution',
                           'filter_out_outlier_sequences',
                           'anvi_get_sequences_for_gene_calls',
                           'fasttree',
                           'iqtree',
                           'run_metagenomics_workflow'
                           ])

        self.general_params.extend(['metagenomes']) # user needs to input a metagenomes.txt file
        self.general_params.extend(['external_genomes']) # user can add isolate genomes if needed
        self.general_params.extend(['external_hmm_list']) # user must input which Reference proteins will be used for workflow


        # Parameters for each rule that are accessible in the config.json file
        rule_acceptable_params_dict = {}

        # rule_acceptable_params_dict['anvi_run_hmms_hmmsearch'] = ['-I']
        rule_acceptable_params_dict['filter_hmm_hits_by_query_coverage'] = ['--hmm-source', '--query-coverage', 'additional_params']
        rule_acceptable_params_dict['anvi_get_sequences_for_hmm_hits_SCGs'] = ['--hmm-source']
        rule_acceptable_params_dict['anvi_estimate_scg_taxonomy_for_SCGs'] = ['--metagenome-mode']
        rule_acceptable_params_dict['remove_redundant_sequences_mmseqs'] = ['--min-seq-id']
        rule_acceptable_params_dict['trim_alignment'] = ['-gt', "-gappyout", 'additional_params']
        rule_acceptable_params_dict['remove_sequences_with_X_percent_gaps'] = ['--max-percentage-gaps']
        rule_acceptable_params_dict['filter_out_outlier_sequences'] = ['-M']
        rule_acceptable_params_dict['fasttree'] = ['run']
        rule_acceptable_params_dict['iqtree'] = ['run', '-m', 'additional_params']
        rule_acceptable_params_dict['run_metagenomics_workflow'] = ['clusterize', 'cluster_submission_params']

        self.rule_acceptable_params_dict.update(rule_acceptable_params_dict)

        # Set default values for parameters accessible in config.json file
        self.default_config.update({
            'metagenomes': 'metagenomes.txt',
            'external_genomes': 'external-genomes.txt',
            'anvi_script_reformat_fasta': {'threads': 5},
            'external_hmm_list': 'external_hmm_list.txt',
            'anvi_run_hmms_hmmsearch': {'threads': 5},
            'filter_hmm_hits_by_query_coverage': {'threads': 5, '--query-coverage': 0.8, '--hmm-source': 'Bacteria_71'},
            'anvi_estimate_scg_taxonomy_for_SCGs': {'threads': 5, '--metagenome-mode': True},
            'filter_for_scg_sequences_and_metadata': {'threads': 5},
            'cat_ribo_proteins_to_one_fasta': {'threads': 5},
            'anvi_get_sequences_for_hmm_hits_SCGs': {'threads': 5, '--hmm-source': 'Bacteria_71'},
            'join_renamed_fasta_with_misc_data': {'threads': 5},
            'remove_redundant_sequences_mmseqs': {'threads': 5, '--min-seq-id': 0.94},
            'align_muscle': {'threads': 5},
            'remove_sequences_with_X_percent_gaps': {'threads': 5, '--max-percentage-gaps': 50},
            'get_gap_count_distribution': {'threads': 5},
            'filter_out_outlier_sequences': {'threads': 5},
            'trim_alignment': {'threads': 5, '-gappyout': True},
            'fasttree': {'run': True, 'threads': 5},
            'iqtree': {'threads': 5,'-m': "MFP"},
            'run_metagenomics_workflow': {'threads': 10, 'clusterize': False}
            })

        # Directory structure for Snakemake workflow
        self.dirs_dict.update({"EXTRACTED_RIBO_PROTEINS_DIR": "EXTERNAL_ECO_PHYLO_WORKFLOW/01_REFERENCE_PROTEIN_DATA"})
        self.dirs_dict.update({"RIBOSOMAL_PROTEIN_FASTAS": "EXTERNAL_ECO_PHYLO_WORKFLOW/02_NR_FASTAS"})
        self.dirs_dict.update({"MSA": "EXTERNAL_ECO_PHYLO_WORKFLOW/03_MSA"})
        self.dirs_dict.update({"RIBOSOMAL_PROTEIN_MSA_STATS": "EXTERNAL_ECO_PHYLO_WORKFLOW/04_SEQUENCE_STATS"})
        self.dirs_dict.update({"TREES": "EXTERNAL_ECO_PHYLO_WORKFLOW/05_TREES"})
        self.dirs_dict.update({"MISC_DATA": "EXTERNAL_ECO_PHYLO_WORKFLOW/06_MISC_DATA"})
        self.dirs_dict.update({"SCG_NT_FASTAS": "EXTERNAL_ECO_PHYLO_WORKFLOW/07_SCG_NT_FASTAS"})
        self.dirs_dict.update({"RIBOSOMAL_PROTEIN_FASTAS_RENAMED": "EXTERNAL_ECO_PHYLO_WORKFLOW/08_RIBOSOMAL_PROTEIN_FASTAS_RENAMED"})


    def init(self):
        """This function is called from within the snakefile to initialize parameters."""

        super().init()

        # Re-assigning LOGS/ dir to inside EXTERNAL_ECO_PHYLO_WORKFLOW/ dir
        self.dirs_dict.update({"LOGS_DIR": "EXTERNAL_ECO_PHYLO_WORKFLOW/00_LOGS"})

        self.names_list = []
        self.names_dirs = []

        # Load metagenomes.txt
        self.metagenomes = self.get_param_value_from_config(['metagenomes'])
        self.input_dirs_dict = {}

        if self.metagenomes:
            filesnpaths.is_file_exists(self.metagenomes)
            try:
                self.metagenomes_df = pd.read_csv(self.metagenomes, sep='\t', index_col=False)
                self.metagenomes_name_list = self.metagenomes_df.name.to_list()
                self.metagenomes_path_list = self.metagenomes_df.contigs_db_path.to_list()
                self.metagenomes_dirname_list = [os.path.dirname(x) for x in self.metagenomes_path_list]
                self.input_dirs_dict.update(dict(zip(self.metagenomes_name_list, self.metagenomes_dirname_list)))
                self.names_dirs.extend(self.metagenomes_dirname_list)
                self.names_list.extend(self.metagenomes_name_list)

            except IndexError as e:
                raise ConfigError("The metagenomes.txt file, '%s', does not appear to be properly formatted. "
                                  "This is the error from trying to load it: '%s'" % (self.metagenomes_df, e))

        # Load external-genomes.txt
        self.external_genomes = self.get_param_value_from_config(['external_genomes'])
        if self.external_genomes:
            filesnpaths.is_file_exists(self.external_genomes)
            try:
                self.external_genomes_df = pd.read_csv(self.external_genomes, sep='\t', index_col=False)
                self.external_genomes_names_list = self.external_genomes_df.name.to_list()
                self.external_genomes_path_list = self.external_genomes_df.contigs_db_path.to_list()
                self.external_genomes_dirname_list = [os.path.dirname(x) for x in self.external_genomes_path_list]
                self.input_dirs_dict.update(dict(zip(self.external_genomes_names_list, self.external_genomes_dirname_list)))
                self.names_dirs.extend(self.external_genomes_dirname_list)
                self.names_list.extend(self.external_genomes_names_list)

            except IndexError as e:
                raise ConfigError("The external-genomes.txt file, '%s', does not appear to be properly formatted. "
                                  "This is the error from trying to load it: '%s'" % (self.external_genomes_df, e))
        else:
            self.external_genomes_names_list = []

        # Make a unique list
        self.names_dirs = list(set(self.names_dirs))

        # Make variables that tells whether we have metagenomes.txt, external-genomes.txt, or both
        if self.metagenomes and not self.external_genomes:
            self.mode = 'metagenomes'
        if not self.metagenomes and self.external_genomes:
            self.mode = 'external_genomes'
        if self.metagenomes and self.external_genomes:
            self.mode = 'both'

        # Load External HMM list
        self.external_hmm_list_path = self.get_param_value_from_config(['external_hmm_list'])
        if self.external_hmm_list_path: 
            filesnpaths.is_file_exists(self.external_hmm_list_path)
            try:
                external_HMM_df = pd.read_csv(self.external_hmm_list_path, sep='\t', index_col=False)
                self.external_HMM_dict = dict(zip(external_HMM_df.name, external_HMM_df.path))

            except IndexError as e:
                raise ConfigError("The external_hmm_list.txt file, '%s', does not appear to be properly formatted. "
                                  "This is the error from trying to load it: '%s'" % (self.Ribosomal_protein_df, e))

            if any("_" in s for s in self.external_HMM_dict.keys()):
                raise ConfigError(f"Please do not use underscores in your external HMM names in: "
                                  f"{self.external_hmm_list_path}")

        # Pick which tree algorithm
        self.run_iqtree = self.get_param_value_from_config(['iqtree', 'run'])
        self.run_fasttree = self.get_param_value_from_config(['fasttree', 'run'])

        if not self.run_iqtree and not self.run_fasttree:
            raise ConfigError("Please choose either iqtree or fasttree in your config file to run your phylogenetic tree.")

        # Decide to clusterize metagenomic workflow
        self.clusterize_metagenomics_workflow = self.get_param_value_from_config(['run_metagenomics_workflow', 'clusterize'])
        self.metagenomics_workflow_HPC_string = self.get_param_value_from_config(['run_metagenomics_workflow', 'cluster_submission_params'])

        self.target_files = self.get_target_files()

    def get_target_files(self):
        target_files = []

        for external_hmm in self.external_HMM_dict.keys():
            target_file = os.path.join(self.dirs_dict['RIBOSOMAL_PROTEIN_FASTAS'], f"{external_hmm}/{external_hmm}_external_gene_calls_all_renamed.tsv")
            target_files.append(target_file)

            # Count num sequences removed per step
            tail_path = f"{external_hmm}_stats.tsv"
            target_file = os.path.join(self.dirs_dict['RIBOSOMAL_PROTEIN_MSA_STATS'], external_hmm, tail_path)
            target_files.append(target_file)

            # Import state file to customize interactive interface
            target_file = os.path.join(f"{external_hmm}_state_imported.done")
            target_files.append(target_file)

            # Reformat names to match splits in interactive interface
            target_file = os.path.join(f"{external_hmm}_combined.done")
            target_files.append(target_file)

            target_file = os.path.join(self.dirs_dict['MISC_DATA'], f"{external_hmm}_misc.tsv")
            target_files.append(target_file)

            # The FINAL trees :)
            # iq-tree
            if self.run_iqtree == True:
                tail_path = "%s.iqtree" % (external_hmm)
                target_file = os.path.join(self.dirs_dict['TREES'], external_hmm, tail_path)
                target_files.append(target_file)
            # fasttree
            elif self.run_fasttree == True:
                tail_path = "%s.nwk" % (external_hmm)
                target_file = os.path.join(self.dirs_dict['TREES'], external_hmm, tail_path)
                target_files.append(target_file)

        return target_files