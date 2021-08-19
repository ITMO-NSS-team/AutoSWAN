import math
import os
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np


def format_datetime(stamp: datetime, monthly=False):
    details = f'{stamp.day:02d}.{stamp.hour:02d}{stamp.minute:02d}{stamp.second:02d}' if not monthly else ''
    return f'{stamp.year}{stamp.month:02d}{details}'


def parse_datetime(datetime_str: str):
    return datetime.strptime(datetime_str, '%Y%m%d.%H%M^S')


def output_to_netcdf(input_path: str, output_path: str, config: 'SwanConfig'):
    hs = np.genfromtxt(input_path)

    time_steps_num = math.floor(hs.shape[0] / config.grid.y_cells)

    # NC file setup
    nc_file = nc.Dataset(os.path.join(os.getcwd(), output_path), 'w', format='NETCDF4')
    nc_file.description = 'SWAN model simulation results'

    # dimensions
    nc_file.createDimension('lat', config.grid.y_cells)
    nc_file.createDimension('lon', config.grid.x_cells)
    nc_file.createDimension('time', None)

    # variables
    latitudes = nc_file.createVariable('lat', 'float32', ('lat',))
    longitudes = nc_file.createVariable('lon', 'float32', ('lon',))
    time = nc_file.createVariable('time', 'float32', ('time',))
    variable = nc_file.createVariable('hs', 'float32', ('lat', 'lon', 'time'), fill_value=-9.0)

    calendar = 'standard'
    units = 'days since 1970-01-01 00:00'
    time.calendar = time
    time.units = units

    # TODO support all time steps
    time_steps = [config.task.simulation_start + timedelta(hours=x) for x in range(time_steps_num)]

    time[:] = nc.date2num(time_steps, units=units, calendar=calendar)

    variable.units = 'm'

    # set the variables we know first
    latitudes[:] = ([config.grid.max_y - config.grid.y_step_deg * i
                     for i in range(config.grid.y_cells)])
    longitudes[:] = [config.grid.min_x + config.grid.x_step_deg * i
                     for i in range(config.grid.x_cells)]

    for ts in range(time_steps_num):
        start = ts * config.grid.y_cells
        end = (ts + 1) * config.grid.y_cells
        variable_for_timestep = hs[start:end]
        variable[:, :, ts] = variable_for_timestep

    nc_file.close()
