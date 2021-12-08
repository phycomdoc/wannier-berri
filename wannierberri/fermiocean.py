import numpy as np
from .__utility import  alpha_A,beta_A, TAU_UNIT
from collections import defaultdict
from . import __result as result
from math import ceil
from . import covariant_formulak as frml
from .formula import FormulaProduct
from . import covariant_formulak_basic as frml_basic
from itertools import permutations
from scipy.constants import Boltzmann, elementary_charge, hbar, electron_mass, physical_constants, angstrom
bohr_magneton = elementary_charge * hbar / (2 * electron_mass)
bohr = physical_constants['Bohr radius'][0] / angstrom
eV_au = physical_constants['electron volt-hartree relationship'][0]
Ang_SI = angstrom

fac_ahc = -1e8 * elementary_charge ** 2 / hbar
fac_spin_hall = fac_ahc * -0.5
factor_ohmic=(elementary_charge/Ang_SI/hbar**2  # first, transform to SI, not forgeting hbar in velocities - now in  1/(kg*m^3)
                 *elementary_charge**2*TAU_UNIT  # multiply by a dimensional factor - now in A^2*s^2/(kg*m^3*tau_unit) = S/(m*tau_unit)
                   * 1e-2  ) # now in  S/(cm*tau_unit)
factor_Hall_classic=elementary_charge**2*Ang_SI/hbar**3  # first, transform to SI, not forgeting hbar in velocities - now in  m/(J*s^3)
factor_Hall_classic*=elementary_charge**3/hbar*TAU_UNIT**2  # multiply by a dimensional factor - now in A^3*s^5*cm/(J^2*tau_unit^2) = S/(T*m*tau_unit^2)
factor_Hall_classic*=1e-2   #  finally transform to S/(T*cm*tau_unit^2)

delta_f =  np.eye(3)

def cumdos(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return FermiOcean(frml.Identity(),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*data_K.cell_volume

def dos(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return FermiOcean(frml.Identity(),data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*data_K.cell_volume

def Hall_morb_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    factor=-Ang_SI*elementary_charge/(2*hbar) # first, transform to SI, not forgettint e/2hbar multilier for morb - now in A*m/J ,restoring the sign of spin magnetic moment
    factor*=elementary_charge**2/hbar  # multiply by a dimensional factor - now in S/(T*m)
    factor*=-1
    factor*=1e-2   #  finally transform to S/(T*cm)
    formula_1  = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula) ,frml.Morb_Hpm(data_K,sign=+1,**kwargs_formula)], name='berry-morb_Hpm')
    formula_2  = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula) ,frml.Omega(data_K,**kwargs_formula)], name='berry-berry')
    res =  FermiOcean(formula_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res += -2* FermiOcean(formula_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)().mul_array(Efermi)
    return res*factor

def Hall_spin_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    factor=-bohr_magneton/(elementary_charge*Ang_SI) # first, transform to SI - now in 1/(m*T) ,restoring the sign of spin magnetic moment
    factor*=-1
    factor*=elementary_charge**2/hbar  # multiply by a dimensional factor - now in S/(T*m)
    factor*=1e-2   #  finally transform to S/(T*cm)
    formula = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula),frml.Spin(data_K)], name='berry-spin')
    return  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*factor

def AHC(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return  FermiOcean(frml.Omega(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*fac_ahc

def AHC_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    res =  FermiOcean(frml_basic.tildeFc(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res*fac_ahc


def spin(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return FermiOcean(frml.Spin(data_K),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()


def Hplus_der(data_K,Efermi, tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    res =  FermiOcean(frml.DerMorb(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)  # swap axes to be consistent with the eq. (30) of DOI:10.1038/s41524-021-00498-5
    return res

def Hplus_der_test(data_K,Efermi, tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    res =  FermiOcean(frml_basic.tildeHGc_d(data_K,sign=+1,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)  # swap axes to be consistent with the eq. (30) of DOI:10.1038/s41524-021-00498-5
    return res



def gme_orb_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula_1  = FormulaProduct ( [frml.Morb_Hpm(data_K,sign=+1,**kwargs_formula) ,data_K.covariant('Ham',commader=1)], name='morb_Hpm-vel')
    formula_2  = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula) ,data_K.covariant('Ham',commader=1)], name='berry-vel')
    res =  FermiOcean(formula_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res += -2* FermiOcean(formula_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)().mul_array(Efermi)
    res.data= np.swapaxes(res.data,1,2)* -elementary_charge**2/(2*hbar)  # swap axes to be consistent with the eq. (29) of DOI:10.1038/s41524-021-00498-5
    return res

def gme_orb(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    Hp = Hplus_der(data_K,Efermi,tetra=tetra,**kwargs_formula).data
    D = berry_dipole(data_K,Efermi,tetra=tetra,**kwargs_formula).data
    tensor_K = - elementary_charge**2/(2*hbar)*(Hp - 2*Efermi[:,None,None]*D  )
    return result.EnergyResult(Efermi,tensor_K,TRodd=False,Iodd=True)

def gme_orb_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    Hp = Hplus_der_test(data_K,Efermi,tetra=tetra,**kwargs_formula).data
    D = berry_dipole_test(data_K,Efermi,tetra=tetra,**kwargs_formula).data
    tensor_K = - elementary_charge**2/(2*hbar)*(Hp - 2*Efermi[:,None,None]*D  )
    return result.EnergyResult(Efermi,tensor_K,TRodd=False,Iodd=True)


def gme_spin_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula  = FormulaProduct ( [frml.Spin(data_K),data_K.covariant('Ham',commader=1)], name='spin-vel')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)* -bohr_magneton/Ang_SI**2  # swap axes to be consistent with the eq. (30) of DOI:10.1038/s41524-021-00498-5
    return res

def gme_spin(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula  = FormulaProduct ( [frml.DerSpin(data_K)], name='derspin')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)* -bohr_magneton/Ang_SI**2  # swap axes to be consistent with the eq. (30) of DOI:10.1038/s41524-021-00498-5
    return res

def Morb(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    fac_morb =  -eV_au/bohr**2
    return    (
                FermiOcean(frml.Morb_Hpm(data_K,sign=+1,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)() 
            - 2*FermiOcean(frml.Omega(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)().mul_array(Efermi) 
                   )  *  (data_K.cell_volume*fac_morb)


def Morb_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    fac_morb =  -eV_au/bohr**2
    return    (
                FermiOcean(frml_basic.tildeHGc(data_K,sign=+1,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)() 
            - 2*FermiOcean(frml_basic.tildeFc(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)().mul_array(Efermi) 
                   )  *  (data_K.cell_volume*fac_morb)

def spin_hall(data_K,Efermi,spin_current_type,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return FermiOcean(frml.SpinOmega(data_K,spin_current_type,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)() * fac_spin_hall

def spin_hall_qiao(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return spin_hall(data_K,Efermi,"qiao",tetra=tetra,**kwargs_formula)

def spin_hall_ryoo(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    return spin_hall(data_K,Efermi,"ryoo",tetra=tetra,**kwargs_formula)

def ohmic_fsurf(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma10tau1 fermi surface"""
    velocity =  data_K.covariant('Ham',commader=1)
    formula  = FormulaProduct ( [velocity,velocity], name='vel-vel')
    return FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*factor_ohmic

def ohmic(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma10tau1 fermi sea"""
    formula =  frml.InvMass(data_K)
    return FermiOcean(formula,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*factor_ohmic

def linear_magnetoresistance_fsurf(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma11tau1 fermi surface"""
    velocity =  data_K.covariant('Ham',commader=1)
    formula  = FormulaProduct ( [velocity,frml.Omega(data_K,**kwargs_formula),velocity], name='vel-vel-berry (aub)')
    res = FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = res.data.transpose(0,1,3,2)
    res.data = res.data*(1 - delta_f[None,None,:,:] - delta_f[None,:,None,:]) 
    return res

def linear_magnetoresistance(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma11tau1 fermi sea (abu) """
    velocity =  data_K.covariant('Ham',commader=1)
    formula1  = FormulaProduct ( [frml.InvMass(data_K),frml.Omega(data_K,**kwargs_formula)], name='mass-berry (abu)')
    formula2  = FormulaProduct ( [velocity,frml.DerOmega(data_K,**kwargs_formula)], name='vel-der_berry (aub)')
    res = FermiOcean(formula1,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2 = FermiOcean(formula2,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = (res.data + res2.data.transpose(0,1,3,2))*(1 - delta_f[None,None,:,:] - delta_f[None,:,None,:]) 
    return res


def Hall_classic_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma11tau2 fermi surface"""
    formula = FormulaProduct ( [data_K.covariant('Ham',commader=1),frml.InvMass(data_K),data_K.covariant('Ham',commader=1)], name='vel-mass-vel')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*factor_Hall_classic
    res.data=res.data[:,:,:,beta_A,alpha_A]-res.data[:,:,:,alpha_A,beta_A]
    res.data=-0.5*(res.data[:,alpha_A,beta_A,:]-res.data[:,beta_A,alpha_A,:])
    res.rank-=2
    return res

def Hall_classic(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma11tau2 fermi sea"""
    formula1 = FormulaProduct ( [frml.InvMass(data_K),frml.InvMass(data_K)], name='mass-mass')
    res =  FermiOcean(formula1,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*factor_Hall_classic
    res.data = res.data.transpose(0,4,1,2,3)
    res.data = res.data[:,:,:,beta_A,alpha_A]-res.data[:,:,:,alpha_A,beta_A]
    res.data=-0.5*(res.data[:,alpha_A,beta_A,:]-res.data[:,beta_A,alpha_A,:])
    res.rank-=2
    return res

def quadra_magnetoresistance_fsurf(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma12au1 fermi surf (abuv) """
    velocity =  data_K.covariant('Ham',commader=1)
    formula  = FormulaProduct ( [velocity,velocity,frml.Omega(data_K,**kwargs_formula),frml.Omega(data_K,**kwargs_formula)],
            name='vel-vel-berry-berry (abuv)')
    res = FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = res.data*(delta_f[None,None,:,None,:] - 1 - delta_f[None,:,None,:,None]*delta_f[None,None,:,None,:]
            +delta_f[None,:,None,:,None]) 
    return res

def quadra_magnetoresistance(data_K,Efermi,kpart=None,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma12au1 fermi sea (abuv) """
    velocity =  data_K.covariant('Ham',commader=1)
    formula1  = FormulaProduct ( [frml.InvMass(data_K),frml.Omega(data_K,**kwargs_formula),frml.Omega(data_K,**kwargs_formula)],
            name='mass-berry-berry (abuv)')
    formula2 = FormulaProduct ( [velocity,frml.DerOmega(data_K,**kwargs_formula),frml.Omega(data_K,**kwargs_formula)],
            name='vel-der_berry-berry (aubv)(avbu)')
    res = FermiOcean(formula1,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2 = FermiOcean(formula2,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = res.data + res2.data.transpose(0,1,3,2,4) + res2.data.transpose(0,1,3,4,2)
    res.data = res.data*(delta_f[None,None,:,None,:] - 1 - delta_f[None,:,None,:,None]*delta_f[None,None,:,None,:]
            +delta_f[None,:,None,:,None]) 
    return res

def berry_dipole_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma20tau1 fermi surface"""
    formula  = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula),data_K.covariant('Ham',commader=1)], name='berry-vel')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)  # swap axes to be consistent with the eq. (29) of DOI:10.1038/s41524-021-00498-5
    return res

def berry_dipole(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma20tau1 fermi sea"""
    res =  FermiOcean(frml.DerOmega(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)  # swap axes to be consistent with the eq. (29) of DOI:10.1038/s41524-021-00498-5
    return res

def berry_dipole_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r""" sigma20tau1 fermi sea"""
    res =  FermiOcean(frml_basic.tildeFc_d(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data= np.swapaxes(res.data,1,2)  # swap axes to be consistent with the eq. (29) of DOI:10.1038/s41524-021-00498-5
    return res

def Der3E(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma20tau2 fermi sea """
    res =  FermiOcean(frml.Der3E(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res

def Der3E_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma20tau2 fermi surface """
    formula  = FormulaProduct ([frml.InvMass(data_K),data_K.covariant('Ham',commader=1)], name='mass-vel')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res

def Der3E_fder2(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma20tau2 fder=2 """
    formula  = FormulaProduct ( [data_K.covariant('Ham',commader=1),data_K.covariant('Ham',commader=1),data_K.covariant('Ham',commader=1)], name='vel-vel-vel')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=2,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()*0.5
    return res

def Nonlinear_Hall_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma21tau1 fermi surface (dbu)"""
    velocity =  data_K.covariant('Ham',commader=1)
    formula  = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula),frml.Omega(data_K,**kwargs_formula),velocity],
            name='berry-berry-vel (udb)')
    res =  FermiOcean(formula,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = (delta_f[None,None,:,:] - 1)*res.data.transpose(0,2,3,1)
    return res

def Nonlinear_Hall(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma21tau1 fermi sea (dbu)"""
    velocity =  data_K.covariant('Ham',commader=1)
    formula1 = FormulaProduct ( [frml.Omega(data_K,**kwargs_formula),frml.DerOmega(data_K,**kwargs_formula)],
            name='berry-der_berry (udb)')
    formula2 = FormulaProduct ( [frml.DerOmega(data_K,**kwargs_formula),frml.Omega(data_K,**kwargs_formula)],
            name='der_berry-berry (ubd)')
    res =  FermiOcean(formula1,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2 =  FermiOcean(formula2,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = (delta_f[None,None,:,:] - 1)*(res.data.transpose(0,2,3,1) +res2.data.transpose(0,3,2,1))
    return res
  

def eMChA_fder2_term1(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma21tau2 fder2 (daspu)"""
    N = None
    velocity =  data_K.covariant('Ham',commader=1)
    formula1_1  = FormulaProduct ( [velocity,frml.Omega(data_K,**kwargs_formula),velocity,velocity],
            name='vel-berry-vel-vel (aups)')
    formula1_2 = FormulaProduct ( [velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='vel-berry-mass (aups)')
    res =  FermiOcean(formula1_1,data_K,Efermi,tetra,fder=2,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res1_2 =  FermiOcean(formula1_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = -2*(res.data + res1_2.data)

    formula2_1  = FormulaProduct( [frml.delta_f(),velocity,frml.Omega(data_K,**kwargs_formula),velocity,velocity],
            name='delta-vel-berry-vel-vel (aubbps)')
    formula2_2  = FormulaProduct( [frml.delta_f(),velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='delta-vel-berry-mass (aubbps)')
    res2_1 =  FermiOcean(formula2_1,data_K,Efermi,tetra,fder=2,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2_2 =  FermiOcean(formula2_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term2 = (res2_1.data + res2_2.data)
    res.data += np.einsum('naubbps->naups',term2)

    term3 = 2*(res2_1.data + res2_2.data).transpose(0,3,1,4,5,6,2) #from usabbp
    res.data += np.einsum('naubbps->naups',term3)


    formula5  = FormulaProduct( [frml.delta_f(),velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='delta-vel-derberry-vel (usabpb)')
    res5 =  FermiOcean(formula5,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term5 = res5.data.transpose(0,3,1,4,6,5,2) # to aubbps 
    res.data += np.einsum('naubbps->naups',term5)

    formula6  = FormulaProduct( [velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='vel-derberry-vel (aups)')
    res6 =  FermiOcean(formula6,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data += res6.data

    #cross product
    formula4_1  = FormulaProduct( [velocity,frml.Omega(data_K,**kwargs_formula),velocity,velocity],
            name='vel-berry-vel-vel (tdxs)') #Civita: pda  tux 
    formula4_2 = FormulaProduct( [velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='vel-berry-mass (tdxs)') #Civita: pda  tux 
    res4_1 =  FermiOcean(formula4_1,data_K,Efermi,tetra,fder=2,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res4_2 =  FermiOcean(formula4_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term4 = (res4_1.data + res4_2.data).transpose(0,2,1,3,4) # to dtxs
    term4 = term4[:,:,beta_A,alpha_A,:]-term4[:,:,alpha_A,beta_A,:] # to dus

    res.data = res.data[:,N,:,:,:,:] + term4[:,:,N,:,N,:]
    res.rank +=1
    return res

def eMChA_fsurf_term1(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    r"""sigma21tau2 fermi surface (daspu)"""
    N = None
    velocity =  data_K.covariant('Ham',commader=1)
    formula1_1  = FormulaProduct ( [velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='vel-der_berry-vel (aups)')
    formula1_2 = FormulaProduct ( [velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='vel-berry-mass (suap)')
    res =  FermiOcean(formula1_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res1_2 =  FermiOcean(formula1_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data = -2*(res.data + res1_2.data.transpose(0,3,2,4,1))

    formula2_1  = FormulaProduct( [frml.delta_f(),velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='delta-vel-der_berry-vel (aubbps)')
    formula2_2  = FormulaProduct( [frml.delta_f(),velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='delta-vel-berry-mass (subbap)')
    res2_1 =  FermiOcean(formula2_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2_2 =  FermiOcean(formula2_2,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term2 = (res2_1.data + res2_2.data.transpose(0,5,2,3,4,6,1))
    res.data += np.einsum('naubbps->naups',term2)

    term3 = 2*(res2_1.data + res2_2.data.transpose(0,5,2,3,4,6,1)).transpose(0,3,1,4,5,6,2) #from usabbp
    res.data += np.einsum('naubbps->naups',term3)


    formula5  = FormulaProduct( [frml.delta_f(),velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='delta-vel-derberry-vel (usabpb)')
    res5 =  FermiOcean(formula5,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term5 = res5.data.transpose(0,3,1,4,6,5,2) # to aubbps 
    res.data += np.einsum('naubbps->naups',term5)

    formula6  = FormulaProduct( [velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='vel-derberry-vel (aups)')
    res6 =  FermiOcean(formula6,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data += res6.data

    #cross product
    formula4_1  = FormulaProduct( [velocity,frml.DerOmega(data_K,**kwargs_formula),velocity],
            name='vel-der_berry-vel (tdxs)') #Civita: pda  tux 
    formula4_2 = FormulaProduct( [velocity,frml.Omega(data_K,**kwargs_formula),frml.InvMass(data_K)],
            name='vel-berry-mass (xdts)') #Civita: pda  tux 
    res4_1 =  FermiOcean(formula4_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res4_2 =  FermiOcean(formula4_1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    term4 = (res4_1.data + res4_2.data.transpose(0,3,2,1,4)).transpose(0,2,1,3,4) # to dtxs
    term4 = term4[:,:,beta_A,alpha_A,:]-term4[:,:,alpha_A,beta_A,:] # to dus

    res.data = res.data[:,N,:,:,:,:] + term4[:,:,N,:,N,:]
    res.rank +=1
    return res

def ddO_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    res =  FermiOcean(frml.Der2Omega(data_K,**kwargs_formula),data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res

def ddO_test_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula1  = FormulaProduct ( [frml.DerOmega(data_K,**kwargs_formula),data_K.covariant('Ham',commader=1)],
            name='vel-derder_berry')
    res =  FermiOcean(formula1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res


def dO_test_fsurf(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula1  = FormulaProduct ( [ data_K.covariant('Ham',commader=1),frml.Omega(data_K,**kwargs_formula),data_K.covariant('Ham',commader=1)],
            name='vel-berry-vel')
    res =  FermiOcean(formula1,data_K,Efermi,tetra,fder=1,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    return res

def dO_test(data_K,Efermi,tetra=False,degen_thresh=1e-4,degen_Kramers=False,**kwargs_formula):
    formula1  = FormulaProduct ( [frml.InvMass(data_K),frml.Omega(data_K,**kwargs_formula)],
            name='mass-berry')
    formula2  = FormulaProduct ( [data_K.covariant('Ham',commader=1),frml.DerOmega(data_K,**kwargs_formula)],
            name='vel-der_berry')
    res =  FermiOcean(formula1,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res2 =  FermiOcean(formula2,data_K,Efermi,tetra,fder=0,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)()
    res.data=res.data.transpose(0,1,3,2) +res2.data
    return res


##################################
### The private part goes here  ##
##################################




class FermiOcean():
    """ formula should have a trace(ik,inn,out) method 
    fder derivative of fermi distribution . 0: fermi-sea, 1: fermi-surface 2: f''
    """

    def __init__(self , formula , data_K,  Efermi, tetra,fder,degen_thresh=1e-4,degen_Kramers=False):

        #print (f"fermiocean using degen_thresh = {degen_thresh}")
        ndim=formula.ndim
        self.Efermi=Efermi
        self.fder=fder
        self.tetra=tetra
        self.nk=data_K.NKFFT_tot
        self.NB=data_K.num_wann
        self.formula=formula
        self.final_factor=1./(data_K.NKFFT_tot * data_K.cell_volume)
        
        # get a list [{(ib1,ib2):W} for ik in op:ed]  
        if self.tetra:
            self.weights=data_K.tetraWeights.weights_all_band_groups(Efermi,der=self.fder,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers)   # here W is array of shape Efermi
        else:
            self.extraEf= 0 if fder==0 else 1 if fder in (1,2) else 2 if fder==3 else None
            self.dEF=Efermi[1]-Efermi[0]        
            self.EFmin=Efermi[ 0]-self.extraEf*self.dEF
            self.EFmax=Efermi[-1]+self.extraEf*self.dEF
            self.nEF_extra=Efermi.shape[0]+2*self.extraEf
            self.weights=data_K.get_bands_in_range_groups(self.EFmin,self.EFmax,degen_thresh=degen_thresh,degen_Kramers=degen_Kramers,sea=(self.fder==0)) # here W is energy
        self.__evaluate_traces(formula, self.weights, ndim )

    def __evaluate_traces(self,formula,bands, ndim):
        """formula  - TraceFormula to evaluate 
           bands = a list of lists of k-points for every 
        """
        self.shape = (3,)*ndim
        lambdadic= lambda: np.zeros(((3, ) * ndim), dtype=float)
        self.values = [defaultdict(lambdadic ) for ik in range(self.nk)]
        for ik,bnd in enumerate(bands):
            if formula.additive:
                 for n in bnd :
                     inn=np.arange(n[0],n[1])
                     out=np.concatenate((np.arange(0,n[0]),np.arange(n[1],self.NB)))
                     self.values[ik][n] = formula.trace(ik,inn,out)
            else:
                 nnall = set([_ for n in bnd for _ in n])
                 _values={}
                 for n in nnall :
                     inn=np.arange(0,n)
                     out=np.arange(n,self.NB)
                     _values[n] = formula.trace(ik,inn,out)
                 for n in bnd:
                     self.values[ik][n] = _values[n[1]] - _values[n[0]]

    def __call__(self) :
        if self.tetra:
            res =  self.__call_tetra()
        else:
            res = self.__call_notetra()
        res *= self.final_factor
        return result.EnergyResult(self.Efermi,res, TRodd=self.formula.TRodd, Iodd=self.formula.Iodd )




    def __call_tetra(self) :
        restot = np.zeros(self.Efermi.shape + self.shape )
        for ik,weights in enumerate(self.weights):
            values = self.values[ik]
            for n,w in weights.items():
                restot+=np.einsum( "e,...->e...",w,values[n] )
        return restot


    def __call_notetra(self) :
        restot = np.zeros((self.nEF_extra,) + self.shape )
        for ik,weights in enumerate(self.weights):
            values = self.values[ik]
            for n,E in sorted(weights.items()):
                if E<self.EFmin:
                    restot += values[n][None]
                elif E<=self.EFmax:
                    iEf=ceil((E-self.EFmin)/self.dEF)
                    restot[iEf:] += values[n]
        if self.fder==0:
            return restot
        if self.fder==1:
            return (restot[2:]-restot[:-2])/(2*self.dEF)
        elif self.fder==2:
            return (restot[2:]+restot[:-2]-2*restot[1:-1])/(self.dEF**2)
        elif self.fder==3:
            return (restot[4:]-restot[:-4]-2*(restot[3:-1]-restot[1:-3]))/(2*self.dEF**3)
        else:
            raise NotImplementedError(f"Derivatives  d^{self.fder}f/dE^{self.fder} is not implemented")


