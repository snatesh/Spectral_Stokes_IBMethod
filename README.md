# Spectral_Stokes_IBMethod
A spectral immersed boundary method for particle suspensions in Stokes flow on doubly and triply periodic domains.

### Build Dependencies ###
You will need to `apt install` at least the following dependencies:

* build-essential
* cmake
* libomp-dev
* gcc 7.5.0 or later (eg. module load gcc-9.2 on cims machines)

### Build Instructions ###
Now, execute the following from the top of the source tree: 
```
$ mkdir build && cd build
$ cmake ..
$ make -j6 (or however many threads you'd like to use)
$ make install
```
Executing the commands above will build all libraries and executables. The libraries are
installed in `$INSTALL_PATH/lib`. Executables are installed in `$INSTALL_PATH/bin`. 
By default, `$INSTALL_PATH` is the top of the source tree.
