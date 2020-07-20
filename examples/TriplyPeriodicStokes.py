# python native stuff
import sys
import random
# import Python modules wrapping C libraries (and also numpy)
sys.path.append('../python')
from Grid import *
from Species import *
from SpreadInterp import *
from Transform import *
from Solvers import TriplyPeriodicStokes

# grid info 
Nx = 64; Ny = 64; Nz = 64; dof = 3 
hx = 0.5; hy = 0.25; hz = 1; 
Lx = Nx * hx; Ly = Ny * hy; Lz = Nz * hz; 
# number of particles
nP = 100
# viscocity
eta = 1/4/np.sqrt(np.pi)
periodicity = 3

# particle positions
xP = np.zeros(3 * nP, dtype = np.double)
# particle forces
fP = np.zeros(dof * nP, dtype = np.double)
# beta for ES kernel for each particle (from table)
betafP = np.zeros(nP, dtype = np.double)
# dimensionless radii given ES kernel for each particle (from table)
cwfP = np.zeros(nP, dtype = np.double)
# width of ES kernel given dimensionless radii (from table)
wfP = np.zeros(nP, dtype = np.ushort)
# actual radii of the particles
radP = np.zeros(nP, dtype = np.double)
# define random configuration of particles
# in terms of kernel, force and position
wf_choices = np.array([4,5,6])
cwf_choices = np.array([1.2047, 1.3437, 1.5539])
betaf_choices = np.array([1.785, 1.886, 1.714])
for iP in np.arange(0,nP):
  # random index
  randInd = random.randrange(np.size(wf_choices)) 
  cwfP[iP] = cwf_choices[randInd]
  wfP[iP] = wf_choices[randInd]
  betafP[iP] = betaf_choices[randInd]
  # set actual radius to same as dimensionless
  # so if h < 1, more than w points will be under the kernel
  radP[iP] = cwfP[iP] 
  xP[3 * iP] = random.random() * (Lx - hx)
  xP[1 + 3 * iP] = random.random() * (Ly - hy)
  xP[2 + 3 * iP] = random.random() * (Lz - hz)
  for j in np.arange(0,dof):
    fP[j + dof * iP] = 10


# instantiate the python grid wrapper
gridGen = GridGen(Lx, Ly, Lz, hx, hy, hz, Nx, Ny, Nz, dof, periodicity)
# instantiate and define the grid with C lib call
# this is a pointer to a C++ struct
grid = gridGen.Make()
# instantiate the python species wrapper
speciesGen = SpeciesGen(nP, dof, xP, fP, radP, wfP, cwfP, betafP)
# instantiate and define the species with C lib call
# this is a pointer to a C++ struct
species = speciesGen.Make()
# setup the species on the grid with C lib call
# this builds the species-grid locator and defines other
# interal data used to spread and interpolate
speciesGen.Setup(species, grid)

# spread forces on the particles (C lib)
fG = Spread(species, grid, gridGen.Ntotal)
# write the grid with spread to file (C lib)
gridGen.WriteGrid(grid, 'spread.txt')
gridGen.WriteCoords(grid, 'coords.txt')  

# instantiate transform wrapper with spread forces (C lib)
fTranformer = Transformer(fG, None, Nx, Ny, Nz, dof)
# compute forward transform (C lib)
forward = fTranformer.Ftransform()
# get the Fourier coefficients (C lib)
fG_hat_r = fTranformer.GetRealOut(forward)
fG_hat_i = fTranformer.GetComplexOut(forward)

# solve Stokes eq 
U_hat_r, U_hat_i = TriplyPeriodicStokes(fG_hat_r, fG_hat_i, eta, Lx, Ly, Lz, Nx, Ny, Nz)

# instantiate back transform wrapper with velocities on grid (C lib)
bTransformer = Transformer(U_hat_r, U_hat_i, Nx, Ny, Nz, dof)
backward = bTransformer.Btransform()
# get real part of back transform and normalize (C lib)
uG_r = bTransformer.GetRealOut(backward) / bTransformer.N

# set velocity as new grid spread (C lib)
gridGen.SetGridSpread(grid, uG_r)

# interpolate velocities on the particles (C lib)
vP = Interpolate(species, grid, nP * dof)

# write species with interpolated vel to file (C lib)
speciesGen.WriteSpecies(species, 'particles.txt')
# write grid velocities
gridGen.WriteGrid(grid, 'velocities.txt')

# free memory persisting b/w C and python (C lib)
fTranformer.Clean(forward)
fTranformer.Delete(forward)
bTransformer.Clean(backward)
bTransformer.Delete(backward)
gridGen.Clean(grid)
gridGen.Delete(grid)
speciesGen.Clean(species)
speciesGen.Delete(species)
