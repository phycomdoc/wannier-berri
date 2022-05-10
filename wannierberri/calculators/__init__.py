"""
The module describes calculators - objects that 
receive :calss:`~wannierberri.data_K.Data_K` objects and yield
:class:`~wannierberri.__result.Result`
"""

import abc
import numpy as np
from wannierberri.result import KBandResult,TABresult

class Calculator(abc.ABC):

    def __init__(self, degen_thresh=1e-4, degen_Kramers=False, save_mode="bin+txt"):
        self.degen_thresh = degen_thresh
        self.degen_Kramers = degen_Kramers
        self.save_mode = save_mode

    @property
    def allow_path(self):
        return False    # change for those who can be calculated on a path instead of a grid

    @abc.abstractmethod
    def __call__(self,data_K):
        pass

class TabulatorAll(Calculator):

    def __init__(self, tabulators, ibands=None, mode="grid"):
        """ tabulators - dict 'key':tabulator
        one of them should be "Energy" """
        self.tabulators = tabulators
        mode = mode.lower()
        assert mode in ("grid","path")
        self.mode = mode
        if "Energy" not in self.tabulators.keys():
            raise ValueError("Energy is not included in tabulators")
        if ibands is not None:
            ibands = np.array(ibands)
        for k, v in self.tabulators.items():
            if v.ibands is None:
                v.ibands = ibands
            else:
                assert v.ibands == ibands

    def __call__(self, data_K):
        return TABresult(
            kpoints=data_K.kpoints_all.copy(),
            mode=self.mode,
            recip_lattice=data_K.system.recip_lattice,
            results={k: v(data_K)
                     for k, v in self.tabulators.items()} )

    @property
    def allow_path(self):
        return self.mode == "path"


from . import static, dynamic, tabulate
