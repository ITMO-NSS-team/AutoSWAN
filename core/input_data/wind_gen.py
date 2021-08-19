import os
from datetime import date

import netCDF4 as nc
import numpy as np

from core.domain.grid import Grid
from core.domain.task import SimulationTask
from core.swan.utils import format_datetime
from core.utils.date import month_range
from core.utils.interpolation import interpolate_data_to_grid
from core.utils.netcdf import time_from_netcdf


def create_wind(grid: Grid, task: SimulationTask,
                initial_wind_template: str,
                final_file_name_template: str,
                storage_path: str):
    year_start = task.spinup_start.year
    year_end = task.simulation_end.year

    if os.path.exists('./data/wind_inventory.txt'):
        return

    for year in range(year_start, year_end + 1, 1):
        start_month, end_month = month_range(year, task)

        for mon in range(start_month, end_month + 1):
            wind_monthly_date = date.fromisoformat(f'{year}-{mon:02d}-01')

            initial_wind = initial_wind_template.format(wind_monthly_date=wind_monthly_date)

            interpolated_wind = f'{storage_path}/int_{grid.grid_id}_wind{wind_monthly_date}.nc'

            if not os.path.exists(interpolated_wind):
                interpolate_data_to_grid(grid, initial_wind, interpolated_wind)

    _wind_to_txt(final_file_name_template, task, grid, storage_path)


def _wind_to_txt(final_file_name_template: str, task: SimulationTask, grid: Grid, storage_path: str,
                 file_splitting_mode='yearly'):
    local_file_names = []

    if file_splitting_mode not in ['yearly', 'monthly']:
        raise NotImplementedError(file_splitting_mode)

    regular_file_name = None

    for year in range(task.spinup_start.year, task.simulation_end.year + 1, 1):
        start_month, end_month = month_range(year, task)

        if file_splitting_mode == 'yearly':
            regular_file_name = final_file_name_template.format(date=f'{year}')
            _process_file(regular_file_name, local_file_names)

        for mon in range(start_month, end_month + 1):

            if file_splitting_mode == 'monthly':
                regular_file_name = final_file_name_template.format(date=f'{year}{mon:02d}')
                _process_file(regular_file_name, local_file_names)

            wind_monthly_date = date.fromisoformat(f'{year}-{mon:02d}-01')

            print(wind_monthly_date)
            interpolated_wind = f'{storage_path}/int_{grid.grid_id}_wind{wind_monthly_date}.nc'

            ncin = nc.Dataset(interpolated_wind, 'r', format='NETCDF4')

            try:
                u10 = np.asarray(ncin.variables['u10'])
                v10 = np.asarray(ncin.variables['v10'])
            except KeyError:
                u10 = np.asarray(ncin.variables['10u'])[:, 0, :, :]
                v10 = np.asarray(ncin.variables['10v'])[:, 0, :, :]

            raw_time = ncin.variables['time']

            time = time_from_netcdf(raw_time)

            timesteps = len(time)

            output_hour_step = 1
            for t in range(timesteps):
                current_time = time[t]

                if (current_time.hour % output_hour_step == 0 and
                        task.spinup_start <= current_time <= task.simulation_end):
                    timestamp = format_datetime(current_time)
                    # f'{current_time.year}{current_time.month:02d}{current_time.day:02d}.{current_time.hour:02d}'
                    print(timestamp)

                    u10_matrix = np.round(u10[t, :, :], 3)
                    v10_matrix = np.round(v10[t, :, :], 3)

                    # TODO take lon/lat direction in nc into account
                    u10_matrix = np.flipud(u10_matrix)
                    v10_matrix = np.flipud(v10_matrix)

                    with open(regular_file_name, 'a') as fin_file:
                        fin_file.write(timestamp)
                        fin_file.write('\n')
                        np.savetxt(fin_file, u10_matrix, delimiter=' ', fmt='%5.2f')
                        np.savetxt(fin_file, v10_matrix, delimiter=' ', fmt='%5.2f')

    np.savetxt(final_file_name_template.format(date='inventory'),
               local_file_names, delimiter='\n', fmt='%s')


def _process_file(regular_file_name, existing_files):
    if os.path.exists(regular_file_name):
        os.remove(regular_file_name)
    existing_files.append(regular_file_name)
    return existing_files
