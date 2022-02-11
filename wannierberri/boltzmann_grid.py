from scipy.constants import elementary_charge, hbar, electron_mass, physical_constants, angstrom #, Boltzmann
from .__finite_differences import FiniteDifferences
import numpy as np
BOHR_MAGNETON_SI = elementary_charge*hbar/(2*electron_mass)

def FermiDirac(E, mu, kBT):
    nkTmax = 30
    res = np.zeros(E.shape)
    sel1= ( E<=mu-nkTmax*kBT )
    sel2= ( E>=mu+nkTmax*kBT )
    sel3 = np.logical_not(sel1+sel2)
    res[sel1] = 1
    res[sel2] = 0
    if kBT >0 :
        res[sel3] =  1.0/(np.exp( (E[sel3]-mu)/kBT ) + 1)
    return res



class Boltzmann_grid():


    def __init__(self,tab_result , mu=0, kBT=0.1, tau =1e-12 ,iband = None, 
                    anomalous_velocity = True,
                    lorentz_force = True , 
                    phase_space_kdot = True,
                    last_term_kdot = True,
                    last_term_rdot = True,
                    zeeman_orb  = True,
                    zeeman_spin = True
                ):
        """
        kBT in eV
        mu in eV
        tau in seconds
            
        """
        self.anomalous_velocity = anomalous_velocity
        self.lorentz_force      = lorentz_force
        self.phase_space_kdot   = phase_space_kdot
        self.last_term_kdot     = last_term_kdot
        self.last_term_rdot     = last_term_kdot
        self.zeeman_orb         = zeeman_orb
        self.zeeman_spin        = zeeman_spin


        self.grid = tab_result.grid
        self.nk = np.prod(self.grid)
        self.inv_cell_vollume = np.linalg.det(tab_result.recip_lattice)/( (2*np.pi)**3 ) * 1e30  # in m^-3
        self.mu  = mu
        self.kBT = kBT
        self.tau = tau
        self.fd  = FiniteDifferences(tab_result.recip_lattice,self.grid)


        self.energ    = tab_result.get_data('Energy')    # energies are in eV
        self.velocity = tab_result.get_data('velocity') * (elementary_charge*1e-10/hbar)   # now velocity is in m/s  (V was in eV*Ang)
        if self.zeeman_orb :
            self.morb    =  tab_result.get_data('morb')   * BOHR_MAGNETON_SI/elementary_charge
            self.dermorb =  tab_result.get_data('dermorb')* BOHR_MAGNETON_SI*1e-10/hbar
        if self.zeeman_spin:
            self.spin    = -tab_result.get_data('spin')   * BOHR_MAGNETON_SI/elementary_charge
            self.derspin = -tab_result.get_data('derspin')* BOHR_MAGNETON_SI*1e-10/hbar
        if self.anomalous_velocity or self.phase_space_kdot or self.last_term_kdot or self.last_term_rdot:
            self.berry = tab_result.get_data('berry')* (1e-20*elementary_charge/hbar)  # curvature in m^2 , multiplied by e/hbar (in SI) , thus resulting A*s^2/kg = 1/Tesla


    def current(self,E=[0,0,0],B = [0,0,0],n_iter = 10):
        " E in V/m, B in Tesla"
        E = np.array(E)
        B = np.array(B)
        energ    = self.energ.copy()
        velocity = self.velocity.copy()
        if self.zeeman_orb:
            energ    += np.dot(self.morb,B)
            velocity += np.dot(B,self.dermorb)
        if self.zeeman_spin:
            energ    += np.dot(self.spin,B)
            velocity += np.dot(B,self.derspin)
#        TODO : correct Berry curvature and orbital moment with positional shift?

        factor = elementary_charge*self.tau/hbar * 1e-10
#        print (f"factor =  {factor}")
        kdot =  np.zeros( self.energ.shape+(3,) )
        for i in range(3):
            kdot[:,:,:,:,i] = E[i]

        if self.lorentz_force:
            kdot +=  np.cross( velocity, B, axisa=-1) 
        if self.last_term_kdot:
            kdot+=   np.dot(E,B)*self.berry
        if self.phase_space_kdot :
            kdot /=  (1+np.dot(self.berry,B))[:,:,:,:,None]
        kdottau = -kdot*factor # should be in Ang^-1

        rdot = velocity
        if self.anomalous_velocity:
            rdot +=  np.cross( E, self.berry , axisb=-1 )
        if self.last_term_rdot:
            rdot+=   np.einsum('xyzna,xyzna,b->xyznb',self.berry, velocity,B)
        f0 = FermiDirac(E=energ, mu=self.mu, kBT=self.kBT)
        f_old = f0.copy()
        f_new = f_old

        current = -np.einsum("abcn,abcnd->d",f_old,rdot)*(self.inv_cell_vollume*elementary_charge / self.nk)
        for n in range(n_iter):
#            print (rdot.shape,kdot.shape,f_old.shape,f_new.shape)
            f_new = f0 - np.einsum("...a,a...->...",kdottau,self.fd.gradient(f_old))
            current = -np.einsum("abcn,abcnd->d",f_new,rdot)*(self.inv_cell_vollume*elementary_charge / self.nk)
#            print (f"iteration {n}  f changed by {np.linalg.norm(f_new-f_old)}  current = {current}")
            f_old = f_new
        return current
