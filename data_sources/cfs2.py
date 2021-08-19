import glob
import os
from calendar import monthrange

import wget

from core.domain.grid import Grid
from core.domain.task import SimulationTask
from core.simulation_case.case_options import DataOptions
from core.utils.cdo import grb2_to_nc, merge_time, split_grib2, subset_vars
from core.utils.date import month_range


def upload_wind_data(data_options: DataOptions,
                     task: SimulationTask,
                     grid: Grid = None):
    """
    :param data_options: options of the data uploading
    :param task: simulation task (that contains dates)
    :param grid: simulation grid
    :return:
    """

    if not os.path.exists(data_options.storage_path):
        os.mkdir(data_options.storage_path)

    for year in range(task.spinup_start.year, task.simulation_end.year + 1):
        start_month, end_month = month_range(year, task)

        for mon in range(start_month, end_month + 1):
            end_day = monthrange(year, mon)[1]

            date_with_mon = f'{year}{mon:02d}'
            new_name_short = f'cfs2u_wind_{date_with_mon}'
            new_nc_file = f'wind_{grid.grid_id}_{year}-{mon:02d}-01.nc'
            # new_nc_file_tmp = f'{data_options.storage_path}/all_{new_name_short}.nc'
            if not os.path.exists(f'{data_options.storage_path}/{new_nc_file}'):
                if not os.path.exists(f'{data_options.storage_path}/all_{new_nc_file}') or \
                        data_options.is_force_overwrite:
                    for day in range(1, end_day + 1):
                        for hr in {0, 6, 12, 18}:
                            try:
                                date = f'{year}{mon:02d}{day:02d}'

                                new_name = f'cfs2u_wind_{date}_{hr:02d}'

                                new_file = f'{data_options.storage_path}/{new_name}.grib2'
                                if (not os.path.exists(new_file) and not os.path.exists(new_nc_file)) \
                                        or data_options.is_force_overwrite:
                                    print(new_file)
                                    raw_file_name = f'cdas1.t{hr:02d}z.sfluxgrbf00.grib2'
                                    url = f'https://www.ncei.noaa.gov/data/climate-forecast-system/access/' \
                                          f'operational-analysis/6-hourly-flux/{year}/{date_with_mon}/{date}/{raw_file_name}'
                                    print(url)
                                    wget.download(url, out=new_file)
                                split_grib2(new_file)
                            except Exception as ex:
                                print(ex)

                if not os.path.exists(f'{data_options.storage_path}/merged_{new_name_short}.grib2'):
                    merge_time(f'{data_options.storage_path}/{new_name_short}*_heightAboveGround.grib2',
                               f'{data_options.storage_path}/merged_{new_name_short}.grib2')

                splitted_files_list = glob.glob(f'{data_options.storage_path}/*grib2_*.grib2')
                for file_path in splitted_files_list:
                    os.remove(file_path)

                if not os.path.exists(f'{data_options.storage_path}/all_{new_nc_file}'):
                    grb2_to_nc(f'{data_options.storage_path}/merged_{new_name_short}.grib2',
                               f'{data_options.storage_path}/all_{new_nc_file}')

                if os.path.exists(f'{data_options.storage_path}/merged_{new_name_short}.grib2'):
                    os.remove(f'{data_options.storage_path}/merged_{new_name_short}.grib2')

                subset_vars(f'{data_options.storage_path}/all_{new_nc_file}',
                            f'{data_options.storage_path}/{new_name_short}.nc',
                            'u10=10u;v10=10v')

                if os.path.exists(f'{data_options.storage_path}/all_{new_nc_file}'):
                    os.remove(f'{data_options.storage_path}/all_{new_nc_file}')

                if os.path.exists(new_name_short):
                    # remove unnecessary grb file
                    os.remove(new_name_short)
