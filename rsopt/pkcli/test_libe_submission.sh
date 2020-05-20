#!/bin/bash
#SBATCH -J myjob
#SBATCH -N 5
#SBATCH -q debug
#SBATCH -A m2783
#SBATCH -o myjob.out
#SBATCH -e myjob.error
#SBATCH -t 00:15:00
#SBATCH -C knl

# Run libEnsemble (manager and 4 workers) on one node
# leaving 4 nodes for worker launched applications.
srun --ntasks 5 --nodes=1 python run_libe.py
