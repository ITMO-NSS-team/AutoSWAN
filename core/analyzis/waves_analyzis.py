import datetime
import os

import matplotlib.pyplot as plt
import pandas as pd

from core.simulation_case.case import Case
from core.swan.utils import format_datetime
from core.utils.netcdf import extract_nearest_ts


class WaveComparer:
    def __init__(self, case: Case, obs_folder: str = 'obs'):
        self.output_files = ['P1']
        self.rean = 'D:\storage\multi_1.ak_10m.hs.201701.nc'
        self.case = case
        self.obs_folder = obs_folder

    def compare_with_rean(self):
        for output_point_file in self.output_files:
            pt_sim_data = pd.read_csv(output_point_file, skiprows=7,
                                      header=None, delimiter=r'\s+', dtype=str)
            dates = [datetime.datetime.strptime(_, '%Y%m%d.%H%M%S') for _ in list(pt_sim_data[0])]
            hs = [float(_) for _ in list(pt_sim_data[2])]

            out_pt = self.case.output_options.target_points[0]
            out_pt_lon, out_pt_lat = out_pt.lon, out_pt.lat
            time_rean, hs_rean = extract_nearest_ts(self.rean, out_pt_lon, out_pt_lat)

            plt.plot(dates, hs)
            plt.plot(time_rean, hs_rean)
            plt.show()

    def compare_with_obs(self):
        for file in os.listdir(self.obs_folder):
            if file.endswith(".csv"):
                obs_file_name = os.path.join(self.obs_folder, file)
                obs_id, obs_var, obs_lat, obs_lon = obs_file_name.replace('.csv', '').split('_')
                obs_lat = float(obs_lat)
                obs_lon = float(obs_lon)
                if obs_var == 'hs':
                    pt_obs_data = pd.read_csv(obs_file_name, delimiter=',')
                    try:
                        time_obs = [datetime.datetime.strptime(_, '%d.%m.%y %H:%M') for _ in list(pt_obs_data['date'])]
                    except:
                        time_obs = [datetime.datetime.strptime(_, '%Y-%m-%d %H:%M:%S') for _ in list(pt_obs_data['date'])]

                    hs_obs = pt_obs_data[obs_var]
                    time_sim, hs_sim = _get_sim_pt_from_field(obs_lon, obs_lat, self.case.case_id,
                                                              self.case.task.simulation_start,
                                                              self.case.task.simulation_end)

                    plt.plot(time_obs, hs_obs, label='Obs')
                    plt.plot(time_sim, hs_sim, label='Model')
                    plt.legend()
                    plt.xticks(rotation=45)
                    plt.show()


def _get_sim_pt(pt_id: str, conf_id: str, start_date: datetime, end_date: datetime):
    output_point_file = \
        f'./results/{pt_id}_{conf_id}_{format_datetime(start_date)}_{format_datetime(end_date)}.tab'
    pt_sim_data = pd.read_csv(output_point_file, skiprows=7,
                              header=None, delimiter=r'\s+', dtype=str)
    dates = [datetime.datetime.strptime(_, '%Y%m%d.%H%M%S') for _ in list(pt_sim_data[0])]
    hs = [float(_) for _ in list(pt_sim_data[2])]
    return dates, hs


def _get_sim_pt_from_field(pt_lon, pt_lat, conf_id: str, start_date: datetime, end_date: datetime):
    output_field_file = \
        f'./results/HSig_{conf_id}_{format_datetime(start_date)}_{format_datetime(end_date)}.nc'
    time_sim, hs_sim = extract_nearest_ts(output_field_file, pt_lon, pt_lat)
    return time_sim, hs_sim
