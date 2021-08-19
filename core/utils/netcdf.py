import os
from typing import Any, Optional

import netCDF4 as nc
import numpy as np

from core.utils.geo import coords_with_data, get_nearest_index


def time_from_netcdf(time_var):
    t_unit = time_var.units  # get unit e.g. "days since 1950-01-01T00:00:00Z"
    try:
        t_cal = time_var.calendar
        return np.asarray(nc.num2date(time_var, units=t_unit, calendar=t_cal))
    except AttributeError:
        return np.asarray(nc.num2date(time_var, units=t_unit))


def get_data_var(nc, var_name: Optional[str] = None):
    # TODO more smart approach
    if var_name is not None:
        return nc[var_name]
    return nc[list(nc.variables.keys())[-1]]


def get_dims(target_path: str):
    nc_file = nc.Dataset(os.path.join(os.getcwd(), target_path), 'r', format='NETCDF4')
    var = get_data_var(nc_file)
    return var.shape


def variable_to_netcdf(grid_lons: Any, grid_lats: Any,
                       var_name: str, var: Optional[np.ndarray], target_path: str):
    if isinstance(grid_lons, list) or len(grid_lons.shape)==1:
        _variable_to_netcdf_regular(grid_lons, grid_lats, var_name, var, target_path)
    else:
        _variable_to_netcdf_curvilinear(grid_lons, grid_lats, var_name, var, target_path)


def _variable_to_netcdf_curvilinear(grid_lons: np.ndarray, grid_lats: np.ndarray,
                                    var_name: str, var: Optional[np.ndarray], target_path: str):
    if var is None:
        var = np.zeros(shape=grid_lons.shape)

    # NC file setup
    nc_file = nc.Dataset(os.path.join(os.getcwd(), target_path), 'w', format='NETCDF4')
    nc_file.description = 'Grid description'

    # dimensions
    nc_file.createDimension('x', grid_lons.shape[1])
    nc_file.createDimension('y', grid_lons.shape[0])

    # variables
    longitudes = nc_file.createVariable('lon', 'double', ('y', 'x'))
    latitudes = nc_file.createVariable('lat', 'double', ('y', 'x'))
    variable = nc_file.createVariable(var_name, 'float32', ('y', 'x'), fill_value=-9.0)

    latitudes.standard_name = 'latitude'
    latitudes.long_name = 'latitude'
    latitudes.units = 'degrees_north'
    latitudes.axis = 'Y'
    latitudes._CoordinateAxisType = "Lat"

    longitudes.standard_name = 'longitude'
    longitudes.long_name = 'longitude'
    longitudes.units = 'degrees_east'
    longitudes.axis = 'X'
    longitudes._CoordinateAxisType = "Lon"

    variable.units = 'logical'
    variable.long_name = 'grid'
    variable.standard_name = 'grid'
    variable.coordinates = 'lat lon'

    # set the variables we know first
    latitudes[:, :] = grid_lats
    longitudes[:, :] = grid_lons
    variable[:, :] = var

    nc_file.close()


def _variable_to_netcdf_regular(grid_lons: list, grid_lats: list,
                                var_name: str, var: Optional[np.ndarray], target_path: str):
    if var is None:
        var = np.zeros(shape=(len(grid_lons), len(grid_lats)))

    # NC file setup
    nc_file = nc.Dataset(os.path.join(os.getcwd(), target_path), 'w', format='NETCDF4')
    nc_file.description = 'Grid description'

    # dimensions
    nc_file.createDimension('x', len(grid_lons))
    nc_file.createDimension('y', len(grid_lats))

    # variables
    longitudes = nc_file.createVariable('lon', 'double', ('x',))
    latitudes = nc_file.createVariable('lat', 'double', ('y',))
    variable = nc_file.createVariable(var_name, 'float32', ('y', 'x'), fill_value=-9.0)

    latitudes.standard_name = 'latitude'
    latitudes.long_name = 'latitude'
    latitudes.units = 'degrees_north'
    latitudes.axis = 'Y'
    latitudes._CoordinateAxisType = "Lat"

    longitudes.standard_name = 'longitude'
    longitudes.long_name = 'longitude'
    longitudes.units = 'degrees_east'
    longitudes.axis = 'X'
    longitudes._CoordinateAxisType = "Lon"

    variable.units = 'logical'
    variable.long_name = 'grid'
    variable.standard_name = 'grid'
    # variable.coordinates = 'lat lon'

    # set the variables we know first
    latitudes[:] = grid_lats
    longitudes[:] = grid_lons
    variable[:, :] = var

    nc_file.close()


def extract_nearest_ts(file_name: str, pt_lon, pt_lat, var_name: Optional[str] = None):
    nc_file = nc.Dataset(file_name, 'r', format='NETCDF4')
    var = get_data_var(nc_file, var_name)
    raw_time = nc_file.variables['time']
    time = time_from_netcdf(raw_time)

    lats = nc_file.variables['lat']
    lons = nc_file.variables['lon']

    data_coords = coords_with_data(lons, lats, var)

    x, y = get_nearest_index(data_coords, pt_lon, pt_lat)

    if var.dimensions[0] == 'time':
        var_ts = var[:, x, y]
    else:
        var_ts = var[x, y, :]

    return time, var_ts
