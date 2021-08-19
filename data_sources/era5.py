import os
from datetime import date
from typing import List, Optional

import cdsapi

from core.domain.grid import Grid
from core.domain.task import SimulationTask
from core.simulation_case.case_options import DataOptions
from core.utils.date import month_range


def era5_wind_request(data_date: date, grid: Optional[Grid], data_options: DataOptions):
    out_name = f'{data_options.storage_path}/wind_{grid.grid_id}_{data_date}.nc'
    data_vars = ['10m_u_component_of_wind', '10m_v_component_of_wind']
    era5_request(data_vars, grid, data_date, out_name, data_options)


def era5_waves_request(data_date: date, grid: Optional[Grid], data_options: DataOptions):
    out_name = f'{data_options.storage_path}/waves_{grid.grid_id}_{data_date.year}{data_date.month:02d}.nc'
    data_vars = ['significant_height_of_combined_wind_waves_and_swell',
                 'peak_wave_period',
                 'mean_wave_direction']
    era5_request(data_vars, grid, data_date, out_name, data_options)


def era5_request(data_vars: List[str], grid: Grid, data_date: date, out_name, data_options: DataOptions):
    """
    Login to CDS (or Login to ADS)
    Copy a 2 line code, which shows a url and your own uid:API key details
    Paste the 2 line code into a  %USERPROFILE%\\.cdsapirc file, where in your windows environment,
    %USERPROFILE% is usually located at C:\\Users\\Username folder).
    For instructions on how to create a dot file on Windows, please see here or check the instructions
    provided by one of users on the User Forum.
    """

    request_coords = [70, 110, -10,
                      360 - 70]
    if grid:
        request_coords = [grid.max_y * 1.05, grid.min_x * 0.95, grid.min_y * 0.95, grid.max_x * 1.05]

    # TODO add coords intersection check

    if (not os.path.exists(out_name)) or data_options.is_force_overwrite:
        print(out_name)
        c = cdsapi.Client()

        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': data_vars,
                'year': str(data_date.year),
                'month': [
                    str(data_date.month)
                ],
                'day': [
                    '01', '02', '03',
                    '04', '05', '06',
                    '07', '08', '09',
                    '10', '11', '12',
                    '13', '14', '15',
                    '16', '17', '18',
                    '19', '20', '21',
                    '22', '23', '24',
                    '25', '26', '27',
                    '28', '29', '30',
                    '31'
                ],
                'time': [
                    '00:00', '01:00', '02:00',
                    '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00',
                    '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00',
                    '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00'
                ],
                'area': request_coords,
            },
            out_name)


def upload_wind_data(data_options: DataOptions,
                     task: SimulationTask,
                     grid: Grid = None):
    for year in range(task.spinup_start.year, task.simulation_end.year + 1):
        start_month, end_month = month_range(year, task)

        for mon in range(start_month, end_month + 1):
            era5_wind_request(date.fromisoformat(f'{year}-{mon:02d}-01'), grid, data_options)


def upload_wave_data(data_options: DataOptions,
                     task: SimulationTask,
                     grid: Grid = None):
    for year in range(task.spinup_start.year, task.simulation_end.year + 1):
        start_month, end_month = month_range(year, task)

        for mon in range(start_month, end_month + 1):
            era5_waves_request(date.fromisoformat(f'{year}-{mon:02d}-01'), grid, data_options)
