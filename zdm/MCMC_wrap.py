"""
File: MCMC_wrap.py
Author: Jordan Hoffmann
Date: 28/09/23
Purpose: 
    Wrapper file to run MCMC analysis for zdm code. Handles command line
    parameters and loading of surveys, grids and parameters. Actual MCMC
    analysis functions are in MCMC.py.

    scripts/run_mcmc.slurm contains an example sbatch script.
"""

import argparse
import os

from zdm import survey
from zdm import cosmology as cos
from zdm.craco import loading
from zdm.MCMC import *

import pickle
import json

import argparse
parser = argparse.ArgumentParser()
parser.add_argument(dest='files', nargs='+', help="Survey file names")
parser.add_argument('-i','--initialise', default=None, type=str, help="Prefix used to initialise survey")
parser.add_argument('-p','--pfile', default=None , type=str, help="File defining parameter ranges")
parser.add_argument('-o','--opfile', default=None, type=str, help="Output file for the data")
parser.add_argument('-w', '--walkers', default=20, type=int, help="Number of MCMC walkers")
parser.add_argument('-s', '--steps', default=100, type=int, help="Number of MCMC steps")
args = parser.parse_args()

# Check correct flags are specified
if args.pfile is None or args.opfile is None:
    if not (args.pfile is None and args.opfile is None):
        print("All flags (except -i optional) are required unless this is only for initialisation in which case only -i should be specified.")
        exit()

#==============================================================================

def main(args):
    names=args.files
    prefix=args.initialise


    ############## Initialise cosmology ##############
    # Location for maximisation output
    outdir='mcmc/'

    cos.init_dist_measures()
    state = loading.set_state()
    
    # get the grid of p(DM|z)
    zDMgrid, zvals,dmvals=get_zdm_grid(state,new=True,plot=False,method='analytic',save=True,datdir='MCMCData')
    
    ############## Initialise surveys ##############

    if not os.path.exists('Pickle/'+prefix+'surveys.pkl'):
        # Initialise surveys
        surveys = []
        for name in names:
            filename = 'data/Surveys/' + name
            s=survey.Survey(state, name, filename, dmvals)

            surveys.append(s)
    
        # Initialise grids
        grids=initialise_grids(surveys,zDMgrid, zvals,dmvals,state,wdist=True)

        # Save surveys / grids in pickle format
        if prefix != None:
            if not os.path.exists('Pickle/'):
                os.mkdir('Pickle/')

            # Save surveys
            print("Saving ",'Pickle/'+prefix+'surveys.pkl')
            with open('Pickle/'+prefix+'surveys.pkl', 'wb') as output:
                pickle.dump(surveys, output, pickle.HIGHEST_PROTOCOL)
                pickle.dump(names, output, pickle.HIGHEST_PROTOCOL)

            # Save grids
            print("Saving ",'Pickle/'+prefix+'grids.pkl')
            with open('Pickle/'+prefix+'grids.pkl', 'wb') as output:
                pickle.dump(grids, output, pickle.HIGHEST_PROTOCOL)
    else:
        print("Loading ",'Pickle/'+prefix+'surveys.pkl')
        # Load surveys
        with open('Pickle/'+prefix+'surveys.pkl', 'rb') as infile:
            surveys=pickle.load(infile)
            names=pickle.load(infile)

        # Load grids
        with open('Pickle/'+prefix+'grids.pkl', 'rb') as infile:
            grids=pickle.load(infile)

    print("Initialised grids and surveys ",names)
    
    # If not initialising only, run mcmc
    if args.pfile is not None and args.opfile is not None:
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        
        with open(args.pfile) as f:
            mcmc_dict = json.load(f)

        # Select from dictionary the necessary parameters to be changed
        params = {k: mcmc_dict[k] for k in mcmc_dict['mcmc']['parameter_order']}

        mcmc_likelihoods(outdir + args.opfile, args.walkers, args.steps, params, surveys, grids)
    else:
        print("No parameter or output file provided. Assuming only initialising and no MCMC running is done.")

main(args)