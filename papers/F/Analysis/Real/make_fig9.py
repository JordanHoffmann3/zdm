"""
This is a script to produce figure 9 for the H0 paper
(James, Ghosh, Prochaska et al)

It requires the original data "Cubefile", available at [repository]

It outputs six plots, all being correlations between H0
and the six other fitted parameters. The slices
obtained are set at the best-fit values of cube parameters.

"""

import numpy as np
import os
import zdm
from zdm import analyze_cube as ac

from matplotlib import pyplot as plt

def main(verbose=False):
    
    # output directory
    opdir="Figure9/"
    if not os.path.exists(opdir):
        os.mkdir(opdir)
    
    CubeFile='Cubes/craco_real_cube.npz'
    if os.path.exists(CubeFile):
        data=np.load(CubeFile)
    else:
        print("Could not file cube output file ",CubeFile)
        print("Please obtain it from [repository]")
        exit()
    
    if verbose:
        print("Data file contains the following items")
        for thing in data:
            print(thing)
    
    lst = data.files
    lldata=data["ll"]
    params=data["params"]

    def get_param_values(data,params):
        """
        Gets the unique values of the data from a cube output
        Currently the parameter order is hard-coded

        """
        param_vals=[]
        for param in params:
            col=data[param]
            unique=np.unique(col)
            param_vals.append(unique)  
        return param_vals
    
    param_vals=get_param_values(data, params)
    
    
    #reconstructs total pdmz given all the pieces, including unlocalised contributions
    pDMz=data["P_zDM0"]+data["P_zDM1"]+data["P_zDM2"]+data["P_zDM3"]+data["P_zDM4"]
    
    #DM only contribution - however it ignores unlocalised DMs from surveys 1-3
    pDMonly=data["pDM"]+data["P_zDM0"]+data["P_zDM4"]
    
    #do this over all surveys
    P_s=data["P_s0"]+data["P_s1"]+data["P_s2"]+data["P_s3"]+data["P_s4"]
    P_n=data["P_n0"]+data["P_n1"]+data["P_n2"]+data["P_n3"]+data["P_n4"]
    
    #labels=['p(N,s,DM,z)','P_n','P(s|DM,z)','p(DM,z)all','p(DM)all','p(z|DM)','p(DM)','p(DM|z)','p(z)']
    #for datatype in [data["ll"],P_n,P_s,pDMz,pDMonly,data["pzDM"],data["pDM"],data["pDMz"],data["pz"]]:
    
    # builds uvals list
    uvals=[]
    latexnames=[]
    for ip,param in enumerate(data["params"]):
        # switches for alpha
        if param=="alpha":
            uvals.append(data[param]*-1.)
        else:
            uvals.append(data[param])
        if param=="alpha":
            latexnames.append('$\\alpha$')
            ialpha=ip
        elif param=="lEmax":
            latexnames.append('$\\log_{10} E_{\\rm max}$')
        elif param=="H0":
            latexnames.append('$H_0$')
        elif param=="gamma":
            latexnames.append('$\\gamma$')
        elif param=="sfr_n":
            latexnames.append('$n_{\\rm sfr}$')
        elif param=="lmean":
            latexnames.append('$\\mu_{\\rm host}$')
        elif param=="lsigma":
            latexnames.append('$\\sigma_{\\rm host}$')
        elif param=="logF":
            latexnames.append('$\\log_{10} F$')
    
    #latexnames=['$\\log_{10} E_{\\rm max}$','$H_0$','$\\alpha$','$\\gamma$','$n_{\\rm sfr}$','$\\mu_{\\rm host}$','$\\sigma_{\\rm host}$']
    
    list2=[]
    vals2=[]
    # gets Bayesian posteriors
    deprecated,uw_vectors,wvectors=ac.get_bayesian_data(data["ll"])
    for i,vec in enumerate(uw_vectors):
        n=np.argmax(vec)
        val=uvals[i][n]
        if params[i] != "logF":
            list2.append(params[i])
            vals2.append(val)
        else:
            iF=i
    
    ###### NOTATION #####
    # uw: unweighted
    # wH0: weighted according to H0 knowledged
    # f: fixed other parameters
    # B: best-fit
    
    ############## 2D plots at best-fit valuess ##########
    
    # gets the slice corresponding to the best-fit values of all other parameters
    # this is 1D, so is our limit on H0 keeping all others fixed
    for i,item in enumerate(list2):
        
        list3=np.concatenate((list2[0:i],list2[i+1:]))
        vals3=np.concatenate((vals2[0:i],vals2[i+1:]))
        array=ac.get_slice_from_parameters(data,list3,vals3)
        
        # log to lin space
        array -= np.max(array)
        array = 10**array
        array /= np.sum(array)
        
        # now have array for slice covering best-fit values
        if i < iF:
            modi=i
        else:
            modi=i+1
            #array=array.T
            array=array.swapaxes(0,1)
        savename=opdir+"/lls_"+params[iF]+"_"+params[modi]+".png"
        
        if params[modi]=="alpha":
            #switches order of array in alpha dimension
            array=np.flip(array,axis=0)
            ac.make_2d_plot(array,latexnames[modi],latexnames[iF],
                -param_vals[modi],param_vals[iF],
                savename=savename,norm=1)
        else:
            ac.make_2d_plot(array,latexnames[modi],latexnames[iF],
                param_vals[modi],param_vals[iF],
                savename=savename,norm=1)
    
main()
