import json
import os
from ast import literal_eval
from datetime import datetime

from core.domain.grid import grid_from_coords, grid_from_txt
from core.domain.task import SimulationTask
from core.input_data.bathy_gen import create_bathy
from core.input_data.bdc_gen import create_bdc
from core.input_data.wind_gen import create_wind
from core.simulation_case.case_options import DataOptions, OutputOptions
from core.swan.swan import SWAN, SwanConfig
from data_sources.cfs2 import upload_wind_data as cfs2_upload_wind_data
from data_sources.era5 import upload_wave_data as era5_upload_wave_data, upload_wind_data
from data_sources.ncar_waves import upload_wave_data as ncar_upload_wave_data


class Case:
    def __init__(self, json_path: str):
        self.is_parallel = False

        with open(json_path, 'r') as file:
            case_data = json.load(file)
            case_description = case_data['case_description']
            simulation = case_data['simulation']

            self.is_parallel = literal_eval(simulation['parallel'])

            self.case_id = case_data['id']
            self.area_description = case_description["area_name"]

            grid = case_description['grid']
            try:
                coords = literal_eval(case_description['coords'])
                self._grid = grid_from_coords(grid_id=self.case_id, coords=coords,
                                              step=int(grid['step']),
                                              step_type=grid['step_unit'],
                                              grid_type=grid['grid_type'])
            except SyntaxError:
                if grid['step_unit'] == 'deg':
                    raise ValueError('Not supported for the grid')
                coords_file_name = case_description['coords']
                self._grid = grid_from_txt(grid_id=self.case_id,
                                           grid_txt_path=coords_file_name,
                                           grid_type=grid['grid_type'],
                                           fixed_step=int(grid['step'])
                                           )

            self._grid.open_boundaries = literal_eval(case_description['open_boundaries'])

            self._data_options = DataOptions(case_data)

            self.output_options = OutputOptions(case_data)

            self.task = SimulationTask(simulation_start=datetime.fromisoformat(simulation['start']),
                                       simulation_end=datetime.fromisoformat(simulation['end']),
                                       spinup_start=datetime.fromisoformat(simulation['spinup_start']),
                                       integration_step=simulation['integration_step'],
                                       model=simulation['model'])

            self.model = SWAN()

    def prepare_case(self):
        print(f'Case {self.case_id} preparation started.')
        print(self.area_description)

        if not os.path.exists('./data'):
            os.mkdir('./data')

        bdc_description = None

        # grid for interpolation
        self._grid.save_as_cdo_grid('./data/grid')

        # bathymetry generation
        create_bathy(self.case_id, self._grid, self._data_options.raw_bathy_path, './data/bathy.bot')

        # input wind upload
        if self._data_options.is_upload_data:
            if self._data_options.wind_dataset_type == 'era5':
                upload_wind_data(data_options=self._data_options,
                                 task=self.task,
                                 grid=self._grid)
            elif self._data_options.wind_dataset_type == 'cfs2':
                cfs2_upload_wind_data(data_options=self._data_options,
                                      task=self.task,
                                      grid=self._grid)
            else:
                raise ValueError('Unknown wind source')

        # input wind generation

        wind_path_template = self._data_options.storage_path + '/wind_' + self._grid.grid_id + '_{wind_monthly_date}.nc'

        create_wind(self._grid, self.task,
                    initial_wind_template=wind_path_template,
                    final_file_name_template='./data/wind_{date}.txt',
                    storage_path=self._data_options.storage_path)

        # wave boundary conditions generation
        if self._grid.open_boundaries:
            if self._data_options.is_upload_data:
                if self._data_options.bdc_dataset_type == 'era5':
                    era5_upload_wave_data(grid=self._grid, data_options=self._data_options,
                                          task=self.task)
                else:
                    ncar_upload_wave_data(data_options=self._data_options,
                                          task=self.task)

            bdc_folder = './data/bdc/'
            if not os.path.exists(bdc_folder):
                os.mkdir(bdc_folder)

            bdc_template_path = f'{self._data_options.storage_path}' + f'/multi_1.' + \
                                self._data_options.bdc_dataset_type + '.{var}.{date}.nc'

            if self._data_options.bdc_dataset_type == 'ww3':
                # TODO remove hardcode
                bdc_template_path = f'{self._data_options.storage_path}' + '/ww3/{year}/ww3.{date}.nc'
            elif self._data_options.bdc_dataset_type == 'era5':
                bdc_template_path = f'{self._data_options.storage_path}' + '/waves_ura_{date}.nc'

            bdc_description = create_bdc(self.case_id, self._grid, self.task,
                                         bathy_path=f'./data/bathy_{self.case_id}.nc',
                                         initial_bdc_template=bdc_template_path,
                                         output_path=f'{bdc_folder}' + '/bdy_{idx}.tpar')

        self._grid.bdc_description = bdc_description

        swan_config = SwanConfig.generate(self.task, self._grid, self.output_options)
        self.model.init_swan_from_template(self.task.model, '.', swan_config)

        print(f'Case {self.case_id} is successfully prepared.')

    def run(self):
        print(f'Case {self.case_id} execution started.')
        self.model.run(is_parallel=self.is_parallel)
        self.model.to_netcdf()
        print(f'Case {self.case_id} is successfully executed.')

    def validate(self):
        raise NotImplementedError()

    def tune(self):
        raise NotImplementedError()
