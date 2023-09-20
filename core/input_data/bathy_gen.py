import os

import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import seaborn as sb

from core.domain.grid import Grid
from core.utils.interpolation import interpolate_data_to_grid
from core.utils.netcdf import variable_to_netcdf


def create_bathy(domain_name: str, grid: Grid, initial_bathy: str, new_bathy: str):
    nc_bathy = f'./data/bathy_{domain_name}.nc'
    nc_bathy_tmp = f'{nc_bathy}.tmp'

    if not os.path.exists(nc_bathy_tmp):
        interpolate_data_to_grid(grid, initial_bathy, nc_bathy_tmp)
    bathy_to_txt(nc_bathy, new_bathy)


def bathy_to_txt(nc_file_name: str, new_name: str, process_as_is=False):
    ncin = nc.Dataset(os.path.join(os.getcwd(), nc_file_name + '.tmp'),
                      'r', format='NETCDF4')

    bathy = np.asarray(ncin.variables['elevation'])

    # TODO take lon/lat direction in nc into account
    bathy = np.flipud(bathy)

    if not process_as_is:
        bathy[bathy != -9] = -bathy[bathy != -9]

    bathy[bathy <= 0] = -9

    btm = np.round(bathy, 1)

    sb.heatmap(btm, cmap='viridis', robust=True)
    plt.show()

    max_len = len(str(int(np.max(bathy)))) + 2
    np.savetxt(new_name, btm, delimiter=' ', fmt=f'%{max_len}.1f')

    saved_lon = np.asarray(ncin['lon'])
    saved_lat = np.flipud(np.asarray(ncin['lat']))
    saved_btm = np.asarray(btm)
    ncin.close()

    variable_to_netcdf(saved_lon, saved_lat, 'elevation',
                                   saved_btm, os.path.join(os.getcwd(), nc_file_name))
