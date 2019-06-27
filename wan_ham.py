#-*- mode: python -*-#
#------------------------------------------------------------#
# This file WAS distributed as part of the Wannier90 code and #
# under the terms of the GNU General Public License. See the #
# file `LICENSE' in the root directory of the Wannier90      #
# distribution, or http://www.gnu.org/copyleft/gpl.txt       #
#                                                            #
# The webpage of the Wannier90 code is www.wannier.org       #
#                                                            #
# The Wannier90 code is hosted on GitHub:                    #
#                                                            #
# https://github.com/wannier-developers/wannier90            #
#------------------------------------------------------------#
#                                                               #
#  Translated to python and adapted for wannier19 project by Stepan Tsirkin #
#                                                               #
#------------------------------------------------------------#

import numpy as np

def fourier_R_to_k(AAA_R,iRvec,NKPT):
    #  AAA_R is an array of dimension ( num_wann x num_wann x nRpts X ... ) (any further dimensions allowed)
    NK=tuple(NKPT)
    nRvec=iRvec.shape[0]
    shapeA=AAA_R.shape
    assert(nRvec==shapeA[2])
    AAA_R=AAA_R.transpose( (2,0,1)+tuple(range(3,len(shapeA)))  )    
    AAA_R=AAA_R.reshape(nRvec,-1)
    AAA_K=np.zeros( NK+(AAA_R.shape[1],), dtype=complex )

    for ir,irvec in enumerate(iRvec):
            AAA_K[tuple(irvec)]=AAA_R[ir]
    for m in range(AAA_K.shape[3]):
            AAA_K[:,:,:,m]=np.fft.fftn(AAA_K[:,:,:,m])
    AAA_K=AAA_K.reshape( (np.prod(NK),)+shapeA[0:2]+shapeA[3:])
    return AAA_K


def get_occ(eig_K,efermi):
    occ=np.zeros(eig_K.shape,dtype=float)
    occ[eig_K<efermi]=1
    return occ

def get_occ_mat_list(UU_k, occ_K=None,efermi=None,eig_K=None):
    if occ_K is None:
        occ_K = get_occ(eig_K, efermi ) 
    f_list=np.einsum("kni,ki,kmi->knm",UU_k,occ_K,UU_k.conj())
    g_list=-f_list.copy()
    for ik in range(g_list.shape[0]):
        g_list[ik]+=np.eye(g_list.shape[1])
    return f_list,g_list


def get_eig(NK,HH_R,iRvec):
    res=get_eig_deleig(NK,HH_R,iRvec)
    return res[0],res[2],res[3]

def  get_eig_deleig(NK,HH_R,iRvec,cRvec=None):
    ## For all  k point on a NK grid this function returns eigenvalues E and
    ## derivatives of the eigenvalues dE/dk_a, using wham_get_deleig_a
    
    num_wann=HH_R.shape[0]
    HH_K=fourier_R_to_k(HH_R,iRvec,NK)
 
    check=np.max( [np.abs(H-H.T.conj()).max() for H in HH_K] )
    if check>1e-10 : raise RuntimeError ("Hermiticity of interpolated Hamiltonian is not good : {0}".format(check))


    EUU=[np.linalg.eigh(Hk) for Hk in HH_K]
    E_K=np.array([euu[0] for euu in EUU])
    UU_K =np.array([euu[1] for euu in EUU])
    print ("Energies calculated")
    
    if cRvec is None: return E_K, None, UU_K, HH_K, None 
    
    delHH_R=HH_R[:,:,:,None]*cRvec[None,None,:,:]
    delHH_K=fourier_R_to_k(delHH_R,iRvec,NK)
    
    delE_K=np.einsum("kml,kmna,knl->kla",UU_K.conj(),delHH_K,UU_K)
    
    return E_K, delE_K, UU_K, HH_K, delHH_K 


def get_JJp_JJm_list(delHH_K, UU_K, eig_K, occ_K=None,efermi=None):
    #===============================================#
    #                                               #
    # Compute JJ^+_a and JJ^-_a (a=Cartesian index) #
    # for a list of Fermi energies                  #
    #                                               #
    #===============================================#

    nk=delHH_K.shape[0]
    num_wann=delHH_K.shape[1]
    delHH_K=np.einsum("kml,kmna,knp->klpa",UU_K.conj(),delHH_K,UU_K)
    
    if occ_K is None and efermi is None:
        raise RuntimeError("either occ or efermi should be specified")
    if not( (occ_K is None) or (efermi is None)):
        raise RuntimeError("either occ or efermi should be specified, NOT BOTH!")
    
    JJp_list=np.zeros( (nk,num_wann,num_wann,3) , dtype=complex )
    JJm_list=np.zeros( (nk,num_wann,num_wann,3) , dtype=complex )
    
    
    for ik in range(nk):
        if efermi is None:
          selm=(occ_K[ik]<0.5)
          seln=(occ_K[ik]>0.5)
        else:
          selm=(eig_K[ik]<efermi)
          seln=(eig_K[ik]>efermi)
        
        sel2d=selm[:,None]*seln[None,:]
        
        for a in range(3):
            JJm_list[ik,sel2d,a]   = 1j*delHH_K[ik,sel2d  ,a]/(eig_K[ik,seln][None,:]-eig_K[ik,selm][:,None]).reshape(-1)
            JJp_list[ik,sel2d.T,a] = 1j*delHH_K[ik,sel2d.T,a]/(eig_K[ik,selm][None,:]-eig_K[ik,seln][:,None]).reshape(-1)
    
    JJp_list=np.einsum("klm,kmna,kpn->klpa",UU_K,JJp_list,UU_K.conj())
    JJm_list=np.einsum("klm,kmna,kpn->klpa",UU_K,JJm_list,UU_K.conj())
    
    return JJp_list, JJm_list



