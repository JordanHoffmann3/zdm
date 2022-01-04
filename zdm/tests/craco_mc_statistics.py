
"""
This generates 1000 MC samples from CRACO.

It's written slightly differently from the standard mc_statistics.py
to make it easier to iterate through different surveys, i.e.
it processes the surveys one at a time.

The main output is the print to screen. This gives the (default 1000)
FRBs and measured redshifts. This has been copied to
CRAFT_CRACO_MC_alpha1_1000.dat (power law)
CRAFT_CRACO_MC_alpha1_gamma_1000.dat (gamma function)

It then also removes the redshift info for all FRBs with DMEG > 1000
and sets z=-1 (z < 0 is code for "unlocalised"), and re-prints the
same list. See
CRAFT_CRACO_MC_alpha1_1000.dat
CRAFT_CRACO_MC_alpha1_gamma_1000.dat

Finally, it also takes one third of all FRBs (irrespective of DM)
and *also* sets z=-1 to simulate FRBs that have not yet been
localised. See
CRAFT_CRACO_MC_alpha1_1000_missing.dat
CRAFT_CRACO_MC_alpha1_gamma_1000_missing.dat


"""


from pkg_resources import resource_filename
import os
import copy
import pickle
import sys
import scipy as sp
import numpy as np
import time
import argparse

from astropy.cosmology import Planck18

from zdm import cosmology as cos
from zdm import misc_functions
from zdm import parameters
from zdm import survey
from zdm import iteration as it
from zdm import beams
from zdm import misc_functions

from IPython import embed

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import matplotlib

from matplotlib.ticker import NullFormatter

matplotlib.rcParams['image.interpolation'] = None

defaultsize=14
ds=4
font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : defaultsize}
matplotlib.rc('font', **font)




def main(N=100,plots=False):
    "created N*survey.NFRBs mock FRBs for all surveys"
    "Input N : creates N*survey.NFRBs"
    "Output : Sample(list) and Surveys(list)"
    
    ############## Initialise parameters ##############
    state = parameters.State()
    
    # Variable parameters
    vparams = {}
    vparams['cosmo'] = {}
    vparams['cosmo']['H0'] = 67.74
    vparams['cosmo']['Omega_lambda'] = 0.685
    vparams['cosmo']['Omega_m'] = 0.315
    vparams['cosmo']['Omega_b'] = 0.044
    
    vparams['FRBdemo'] = {}
    vparams['FRBdemo']['alpha_method'] = 1 #or set to zero for spectral index interpretation
    vparams['FRBdemo']['source_evolution'] = 0
    
    vparams['beam'] = {}
    vparams['beam']['thresh'] = 0
    vparams['beam']['method'] = 2
    
    vparams['width'] = {}
    vparams['width']['logmean'] = 1.70267
    vparams['width']['logsigma'] = 0.899148
    vparams['width']['Wbins'] = 10
    vparams['width']['Wscale'] = 2
    
     # constants of intrinsic width distribution
    vparams['MW']={}
    vparams['MW']['DMhalo']=50
    
    vparams['host']={}
    vparams['energy'] = {}
    
    if vparams['FRBdemo']['alpha_method'] == 0:
        vparams['energy']['lEmin'] = 30
        vparams['energy']['lEmax'] = 41.7
        vparams['energy']['alpha'] = 1.55
        vparams['energy']['gamma'] = -1.09
        vparams['energy']['luminosity_function'] = 1
        vparams['FRBdemo']['sfr_n'] = 1.67
        vparams['FRBdemo']['lC'] = 3.15
        vparams['host']['lmean'] = 2.11
        vparams['host']['lsigma'] = 0.53
    elif  vparams['FRBdemo']['alpha_method'] == 1:
        vparams['energy']['lEmin'] = 30
        vparams['energy']['lEmax'] = 41.4
        vparams['energy']['alpha'] = 0.65
        vparams['energy']['gamma'] = -1.01
        vparams['energy']['luminosity_function'] = 1
        vparams['FRBdemo']['sfr_n'] = 0.73
        vparams['FRBdemo']['lC'] = 1 #not best fit, OK for a once-off
        
        vparams['host']['lmean'] = 2.18
        vparams['host']['lsigma'] = 0.48
        
    state.update_param_dict(vparams)

    ############## Initialise cosmology ##############
    cos.set_cosmology(state)
    cos.init_dist_measures()
    
      # get the grid of p(DM|z). See function for default values.
    # set new to False once this is already initialised
    zDMgrid, zvals,dmvals = misc_functions.get_zdm_grid(
        state, new=True, plot=False, method='analytic')
    
    
    ######## choose which surveys to do an MC for #######
    
    # choose which survey to create an MC for
    names = ['CRAFT/FE', 'CRAFT/ICS', 'CRAFT/ICS892', 'PKS/Mb','CRAFT_CRACO_MC_frbs_alpha1_5000']
    dirnames=['ASKAP_FE','ASKAP_ICS','ASKAP_ICS892','Parkes_Mb','CRACO']
    # select which to perform an MC for
    which=4
    N=1000
    
    samples,surveys=do_mc(state,zvals,dmvals,zDMgrid,N,names[which],dirnames[which],printit=True)
    

def do_mc(state,zvals,dmvals,zDMgrid,Nsamples,names,dirnames,printit=False,plots=False):   
    ############## Initialise surveys ##############
    #saves everything in this directory
    outdir='MC/'
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    
    #These surveys combine time-normalised and time-unnormalised samples 
    #sprefix='Std' # faster - fine for max likelihood calculations, not as pretty
    # insert more control over detail in grid
    names=[names]
    dirnames=[dirnames]
    NewSurveys=True
    if NewSurveys:
        surveys = []
        for survey_name in names:
            surveys.append(survey.load_survey(survey_name, state, dmvals))
        
    print("Initialised surveys ",names)
    
    #gprefix=sprefix
    
    NewGrids=True
    
    if NewGrids:
        print("Generating new grids, set NewGrids=False to save time later")
        grids=misc_functions.initialise_grids(
            surveys,zDMgrid, zvals, dmvals, state, wdist=True)#, source_evolution=source_evolution, alpha_method=alpha_method)
    
    print("Initialised grids")
    
    
    samples = []
    for i in range(len(surveys)):
        # testing_MC!!! Generate pseudo samples from all surveys
        g = grids[i]
        s = surveys[i]
        name = i
        name = str(name)
    
        savefile=outdir+'mc_sample_'+name+'_alpha_'+str(state.FRBdemo.alpha_method)+str(Nsamples)+'.npy'
    
        try:
            sample=np.load(savefile)
            print("Loading ",sample.shape[0]," samples from file ",savefile)
        except:
            print("Generating ",Nsamples," samples from survey/grid ",i)
            sample=g.GenMCSample(Nsamples)
            sample=np.array(sample)
            np.save(savefile,sample)
        print("Shape of samples is ",samples)
        samples.append(sample)
        
        print("########### Set 1: complete ########")
        for j in np.arange(Nsamples):
            DMG=35
            DMEG=sample[j,1]
            DMtot=DMEG+DMG+state.MW.DMhalo
            SNRTHRESH=9.5
            SNR=SNRTHRESH*sample[j,4]
            z=sample[j,0]
            w=sample[j,3]
            
            string="FRB "+str(j)+'  {:6.1f}  35   {:6.1f}  {:5.3f}   {:5.1f}  {:5.1f}'.format(DMtot,DMEG,z,SNR,w)
            #print("FRB ",i,DMtot,SNR,DMEG,w)
            print (string)
        
        print("\n\n\n\n########### Set 2: no z above DM 1000 ########")
        for j in np.arange(Nsamples):
            DMG=35
            DMEG=sample[j,1]
            DMtot=DMEG+DMG+state.MW.DMhalo
            SNRTHRESH=9.5
            SNR=SNRTHRESH*sample[j,4]
            if DMEG > 1000:
                z = -1
            else:
                z = sample[j,0]
            w=sample[j,3]
            
            string="FRB "+str(j)+'  {:6.1f}  35   {:6.1f}  {:5.3f}   {:5.1f}  {:5.1f}'.format(DMtot,DMEG,z,SNR,w)
            #print("FRB ",i,DMtot,SNR,DMEG,w)
            print (string)
        
        print("\n\n\n\n########### Set 3: also one in 3 unlocalised ########")
        for j in np.arange(Nsamples):
            DMG=35
            DMEG=sample[j,1]
            DMtot=DMEG+DMG+state.MW.DMhalo
            SNRTHRESH=9.5
            SNR=SNRTHRESH*sample[j,4]
            if DMEG > 1000 or j%3==0:
                z = -1
            else:
                z = sample[j,0]
            w=sample[j,3]
            
            string="FRB "+str(j)+'  {:6.1f}  35   {:6.1f}  {:5.3f}   {:5.1f}  {:5.1f}'.format(DMtot,DMEG,z,SNR,w)
            #print("FRB ",i,DMtot,SNR,DMEG,w)
            print (string)
        
        if plots:
            #plot some sample plots
            do_basic_sample_plots(sample)
            #evaluate_mc_sample_v1(g,s,pset,sample)
            evaluate_mc_sample_v2(g,s,pset,sample)
        
    return samples,surveys
    
    
def evaluate_mc_sample_v1(grid,survey,pset,sample,opdir='Plots'):
    """
    Evaluates the likelihoods for an MC sample of events
    Simply replaces individual sets of z, DM, s with MC sets
    Will produce a plot of Nsamples/NFRB pseudo datasets.
    """
    t0=time.process_time()
    
    nsamples=sample.shape[0]
    
    # get number of FRBs per sample
    Npersurvey=survey.NFRB
    # determines how many false surveys we have stats for
    Nsurveys=int(nsamples/Npersurvey)
    
    print("We can evaluate ",Nsurveys,"MC surveys given a total of ",nsamples," and ",Npersurvey," FRBs in the original data")
    
    # makes a deep copy of the survey
    s=copy.deepcopy(survey)
    
    lls=[]
    #Data order is DM,z,b,w,s
    # we loop through, artificially altering the survey with the composite values.
    for i in np.arange(Nsurveys):
        this_sample=sample[i*Npersurvey:(i+1)*Npersurvey,:]
        s.DMEGs=this_sample[:,0]
        s.Ss=this_sample[:,4]
        if s.nD==1: # DM, snr only
            ll=it.calc_likelihoods_1D(grid,s,pset,psnr=True,Pn=True,dolist=0)
        else:
            s.Zs=this_sample[:,1]
            ll=it.calc_likelihoods_2D(grid,s,pset,psnr=True,Pn=True,dolist=0)
        lls.append(ll)
    t1=time.process_time()
    dt=t1-t0
    print("Finished after ",dt," seconds")
    
    lls=np.array(lls)
    
    plt.figure()
    plt.hist(lls,bins=20)
    plt.xlabel('log likelihoods [log10]')
    plt.ylabel('p(ll)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(opdir+'/ll_histogram.pdf')
    plt.close()


def evaluate_mc_sample_v2(grid,survey,pset,sample,opdir='Plots',Nsubsamp=1000,title=''):
    """
    Evaluates the likelihoods for an MC sample of events
    First, gets likelihoods for entire set of FRBs
    Then re-samples as needed, a total of Nsubsamp times
    """
    t0=time.process_time()
    
    nsamples=sample.shape[0]
    
    # makes a deep copy of the survey
    s=copy.deepcopy(survey)
    NFRBs=s.NFRB
    
    s.NFRB=nsamples # NOTE: does NOT change the assumed normalised FRB total!
    s.DMEGs=sample[:,1]
    s.Ss=sample[:,4]
    if s.nD==1: # DM, snr only
        llsum,lllist,expected,longlist=it.calc_likelihoods_1D(grid,s,pset,psnr=True,Pn=True,dolist=2)
    else:
        s.Zs=sample[:,0]
        llsum,lllist,expected,longlist=it.calc_likelihoods_2D(grid,s,pset,psnr=True,Pn=True,dolist=2)
    
    # we should preserve the normalisation factor for Tobs from lllist
    Pzdm,Pn,Psnr=lllist
    
    # plots histogram of individual FRB likelihoods including Psnr and Pzdm
    plt.figure()
    plt.hist(longlist,bins=100)
    plt.xlabel('Individual Psnr,Pzdm log likelihoods [log10]')
    plt.ylabel('p(ll)')
    plt.tight_layout()
    plt.title(title)
    plt.savefig(opdir+'/individual_ll_histogram.pdf')
    plt.close()
    
    # generates many sub-samples of the data
    lltots=[]
    for i in np.arange(Nsubsamp):
        thislist=np.random.choice(longlist,NFRBs) # samples with replacement, by default
        lltot=Pn+np.sum(thislist)
        lltots.append(lltot)
    
    plt.figure()
    plt.hist(lltots,bins=20)
    plt.xlabel('log likelihoods [log10]')
    plt.ylabel('p(ll)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(opdir+'/sampled_ll_histogram.pdf')
    plt.close()
    
    t1=time.process_time()
    dt=t1-t0
    print("Finished after ",dt," seconds")
    
    
def do_basic_sample_plots(sample,opdir='Plots',title=''):
    """
    Data order is DM,z,b,w,s
    
    """
    if not os.path.exists(opdir):
        os.mkdir(opdir)
    zs=sample[:,0]
    DMs=sample[:,1]
    plt.figure()
    plt.hist(DMs,bins=100)
    plt.xlabel('DM')
    plt.ylabel('Sampled DMs')
    plt.tight_layout()
    plt.savefig(opdir+'/DM_histogram.pdf')
    plt.title(title)
    plt.close()
    
    plt.figure()
    plt.hist(zs,bins=100)
    plt.xlabel('z')
    plt.ylabel('Sampled redshifts')
    plt.tight_layout()
    plt.savefig(opdir+'/z_histogram.pdf')
    plt.title(title)
    plt.close()
    
    bs=sample[:,2]
    plt.figure()
    plt.hist(np.log10(bs),bins=5)
    plt.xlabel('log10 beam value')
    plt.yscale('log')
    plt.ylabel('Sampled beam bin')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(opdir+'/b_histogram.pdf')
    plt.close()
    
    ws=sample[:,3]
    plt.figure()
    plt.hist(ws,bins=5)
    plt.xlabel('width bin (not actual width!)')
    plt.ylabel('Sampled width bin')
    plt.yscale('log')
    plt.tight_layout()
    plt.title(title)
    plt.savefig(opdir+'/w_histogram.pdf')
    plt.close()
    
    s=sample[:,4]
    plt.figure()
    plt.hist(np.log10(s),bins=100)
    plt.xlabel('$\\log_{10} (s={\\rm SNR}/{\\rm SNR}_{\\rm th})$')
    plt.yscale('log')
    plt.ylabel('Sampled $s$')
    plt.tight_layout()
    plt.title(title)
    
    plt.savefig(opdir+'/s_histogram.pdf')
    plt.close()
    
main()
