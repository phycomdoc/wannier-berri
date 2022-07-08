import numpy as np

def init_mat(system, grid):
    K_list = grid.get_K_list()
    nK_ext = len(K_list)

    nb = system.num_wann
    nk_fft = grid.FFT[0]*grid.FFT[1]*grid.FFT[2]
    npol = 3
    global wint_dipole
    global wDdipole
    wint_dipole = np.zeros([nK_ext, nk_fft, nb, nb, npol], dtype=complex)
    wDdipole = np.zeros([nK_ext, nk_fft, nb, nb, npol,npol], dtype=complex)

    return wint_dipole, wDdipole

def init_mat_fromdata(data):
    K_list = data.gird.get_K_list()
    nK_ext = len(K_list)

    nb = data.num_wann
    nk_fft = data.nk
    npol = 3
    global wint_dipole
    global wDdipole
    wint_dipole = np.zeros([nK_ext, nk_fft, nb, nb, npol], dtype=complex)
    wDdipole = np.zeros([nK_ext, nk_fft, nb, nb, npol,npol], dtype=complex)

    return wint_dipole, wDdipole

count = 0
