import os
import warnings
from ast import literal_eval
from dataclasses import dataclass


class CaseOptions:
    def __init__(self, config: dict):
        self._config = config


class OutputOptions(CaseOptions):
    @property
    def output_config(self):
        return self._config['output']

    @property
    def variables(self):
        return literal_eval(self.output_config['variables'])

    @property
    def is_save_output_fields(self):
        return literal_eval(self.output_config['save_output_fields'])

    @property
    def is_save_spectres(self):
        return literal_eval(self.output_config['save_spectres'])

    @property
    def target_points(self):
        output_points = self.output_config['points']
        if output_points == 'None':
            return {}

        # TODO add check that point inside the domain

        output_points_list = []
        for point_id in output_points.keys():
            pt_info = literal_eval(output_points[point_id])
            point = OutputPoint(name=point_id, lat=pt_info[0], lon=pt_info[1], description=pt_info[2])
            output_points_list.append(point)
        return output_points_list


class DataOptions(OutputOptions):
    _ncep_ncar_wave_datasets = ['glo_30m', 'ao_30m', 'at_10m',
                                'wc_10m', 'ep_10m', 'ak_10m',
                                'at_4m', 'wc_4m', 'ak_4m']

    @property
    def data_config(self):
        return self._config['data']

    @property
    def is_upload_data(self):
        return literal_eval(self.data_config['upload_data'])

    @property
    def storage_path(self):
        path = self.data_config['storage_path']
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @property
    def is_force_overwrite(self):
        return literal_eval(self.data_config['force_overwrite'])

    @property
    def raw_bathy_path(self):
        path = self.data_config['bathy_source']
        return path

    @property
    def bdc_dataset_type(self):
        bdc_data_type = self.data_config['bdc_dataset_type']
        return bdc_data_type

    @property
    def wind_dataset_type(self):
        try:
            bdc_data_type = self.data_config['wind_dataset_type']
        except ValueError:
            warnings.warn('Wind data source not specified, ERA5 used.')
            bdc_data_type = 'era5'
        return bdc_data_type


@dataclass
class OutputPoint:
    lon: float
    lat: float
    name: str
    description: str = 'Output point for simulation'
