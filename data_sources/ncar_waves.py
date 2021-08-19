import os

import wget

from core.domain.task import SimulationTask
from core.simulation_case.case_options import DataOptions
from core.utils.cdo import grb2_to_nc
from core.utils.date import month_range


def upload_wave_data(data_options: DataOptions,
                     task: SimulationTask):
    """
    :param data_options: options of the data uploading
    :param task: simulation task (that contains dates)
    :return:
    """

    if data_options.bdc_dataset_type not in ['glo_30m', 'ao_30m', 'at_10m',
                                             'wc_10m', 'ep_10m', 'ak_10m',
                                             'at_4m', 'wc_4m', 'ak_4m']:
        return

    if not os.path.exists(data_options.storage_path):
        os.mkdir(data_options.storage_path)

    for year in range(task.spinup_start.year, task.simulation_end.year + 1):
        start_month, end_month = month_range(year, task)

        for mon in range(start_month, end_month + 1):
            bdc_vars = ['hs', 'tp', 'dp']
            date = f'{year}{mon:02d}'

            for var in bdc_vars:
                new_file = f'{data_options.storage_path}/multi_1.{data_options.bdc_dataset_type}.{var}.{date}.grb2'
                new_nc_file = f'{data_options.storage_path}/multi_1.{data_options.bdc_dataset_type}.{var}.{date}.nc'
                if (not os.path.exists(new_file) and not os.path.exists(new_nc_file)) \
                        or data_options.is_force_overwrite:
                    print(new_file)
                    url = f'ftp://polar.ncep.noaa.gov/pub/history/waves/multi_1/' \
                          f'{date}/gribs/multi_1.{data_options.bdc_dataset_type}.{var}.{date}.grb2'
                    print(url)
                    wget.download(url, out=new_file)
                if not os.path.exists(new_nc_file) or data_options.is_force_overwrite:
                    grb2_to_nc(new_file, new_nc_file)

                if os.path.exists(new_file):
                    # remove unnecessary grb file
                    os.remove(new_file)
