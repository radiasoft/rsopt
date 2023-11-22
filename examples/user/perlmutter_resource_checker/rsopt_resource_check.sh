#!/bin/bash
#SBATCH -N 1
#SBATCH -C cpu
#SBATCH -q debug
#SBATCH -J rsopt_resource_checker
#SBATCH -t 00:01:00

module load conda
conda activate INSERT_RSOPT_CONDA_ENV
rsopt sample start config_resource_check.yml
