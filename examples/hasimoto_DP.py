# python native stuff
import sys
import random
# import Python modules wrapping C libraries (and also numpy)
sys.path.append('../python')
from Grid import *
from Species import *
from SpreadInterp import *
from Transform import *
from Chebyshev import *
from Solvers import DoublyPeriodicStokes_no_wall

nTrials = 1
Ls = np.linspace(60.,200.,5)
mobx = np.zeros((Ls.size,nTrials), dtype = np.double)
# boundary conditions specified for ends of each axis
BCs = np.array([1,1,1,1,0,0], dtype = np.uintc)
# grid spacing in x,y
hx = hy = 0.5
# chebyshev grid and weights for z
Lz = 20.0; H = Lz / 2.0; 
Nz = int(np.ceil(1.25 * (np.pi / (np.arccos(-hx / H) - np.pi / 2))))
zpts, zwts = clencurt(Nz, 0, Lz)

# if no wall, choose whether to 0 the k=0 mode of the RHS
# k0 = 0 - the k=0 mode of the RHS for pressure and velocity will be 0
# k0 = 1 - the k=0 mode of the RHS for pressure and velocity will not be 0
#        - there will be a correction to the k=0 mode after each solve
k0 = 0;

for iL in range(0,Ls.size):
  for iTrial in range(0,nTrials):
    # grid info 
    Nx = Ny = int(Ls[iL]); dof = 3 
    Lx = Ly = hx * Nx 
    # number of particles
    nP = 1
    # viscocity
    eta = 1/4/np.sqrt(np.pi)
    # particle positions
    xP = np.zeros(3 * nP, dtype = np.double)
    xP[0] = Lx / 2
    xP[1] = Lx / 2
    xP[2] = Lz / 2.0#random.random() * Lz
    print(xP)
    # particle forces
    fP = np.zeros(dof * nP, dtype = np.double)
    fP[0] = 1; fP[1] = 0; fP[2] = 0
    # beta for ES kernel for each particle (from table)
    betafP = np.array([1.714])
    # dimensionless radii given ES kernel for each particle (from table)
    cwfP = np.array([1.5539])
    # width of ES kernel given dimensionless radii (from table)
    wfP = np.array([6], dtype = np.ushort)
    # actual radii of the particles
    radP = hx * np.array([cwfP[0]])
    
    # instantiate the python grid wrapper
    gridGen = GridGen(Lx, Ly, Lz, hx, hy, 0, Nx, Ny, Nz, dof, BCs, zpts, zwts)
    # instantiate and define the grid with C lib call
    # this sets the GridGen.grid member to a pointer to a C++ Grid struct
    gridGen.Make()
    # instantiate the python species wrapper
    speciesGen = SpeciesGen(nP, dof, xP, fP, radP, wfP, cwfP, betafP)
    # instantiate and define the species with C lib call
    # this sets the SpeciesGen.species member to a pointer to a C++ SpeciesList struct
    species = speciesGen.Make()
    # setup the species on the grid with C lib call
    # this builds the species-grid locator and defines other
    # interal data used to spread and interpolate
    speciesGen.Setup(gridGen.grid)
    
    # spread forces on the particles (C lib)
    fG = Spread(speciesGen.species, gridGen.grid, gridGen.Ntotal)
    # instantiate transform wrapper with spread forces (C lib)
    fTransformer = Transformer(fG, None, Nx, Ny, Nz, dof)
    fTransformer.Ftransform_cheb()
    # get the Fourier coefficients
    fG_hat_r = fTransformer.out_real
    fG_hat_i = fTransformer.out_complex
    
    # solve Stokes eq 
    U_hat_r, U_hat_i, _, _ = DoublyPeriodicStokes_no_wall(fG_hat_r, fG_hat_i, eta, Lx, Ly, Lz, Nx, Ny, Nz, k0)
    
    # instantiate back transform wrapper with velocities on grid (C lib)
    bTransformer = Transformer(U_hat_r, U_hat_i, Nx, Ny, Nz, dof)
    bTransformer.Btransform_cheb()
    # get real part of back transform
    uG_r = bTransformer.out_real
    
    # set velocity as new grid spread (C lib)
    gridGen.SetGridSpread(uG_r)
    
    # interpolate velocities on the particles (C lib)
    vP = Interpolate(speciesGen.species, gridGen.grid, nP * dof)
    print(vP)
    
    # save x mobility
    mobx[iL,iTrial] = vP[0] 
 
    # free memory persisting b/w C and python (C lib)
    fTransformer.Clean()
    bTransformer.Clean()
    gridGen.Clean()
    speciesGen.Clean()

np.savetxt('x_mobility_nonUnit_DP.txt', mobx)

