import os
import shutil
import subprocess

import psutil

from core.swan.config import SwanConfig
from core.swan.utils import output_to_netcdf
from core.utils.files import get_project_root


class SWAN:
    _results_folder = 'results'

    def __init__(self, config_name='config', model_folder='.'):
        self._config_name = config_name
        self._model_folder = model_folder
        self._config = None
        self.is_ready = False

    def init_swan_from_template(self, model_id: str, target_folder: str, config: SwanConfig):
        self._config = config

        template_path = f'{get_project_root()}/templates/swan/{model_id}/'
        template_path_common = f'{get_project_root()}/templates/swan/'

        config_template_name = 'config_template.swn'

        template_files = ['swan.exe', 'swan.edt', 'swanrun.bat']

        for file in template_files:
            shutil.copy(f'{template_path}/{file}', target_folder)

        new_config_path = f'{target_folder}/{self._config_name}'

        with open(f'{template_path_common}/{config_template_name}', 'r') as file:
            template_text = file.read()

        filled_template_text = config.fill_template(template_text)

        self._model_folder = target_folder

        with open(f'{new_config_path}.swn', 'w') as file:
            file.write(filled_template_text)

        self.is_ready = True

        print(f'Model {model_id} initialised')

    def run(self, is_parallel=False, verbose=True):
        if not self._model_folder or not self.is_ready:
            raise ValueError('Model folder is not set')

        current_folder = os.getcwd()
        os.chdir(self._model_folder)

        self._clean_output()

        if not os.path.exists(self._results_folder):
            os.mkdir(self._results_folder)

        params = {'shell': True}
        if not verbose:
            params['stdout'] = subprocess.DEVNULL

        num_cores = psutil.cpu_count()

        if is_parallel:
            subprocess.run(fr'swanrun.bat {self._config_name} -n {num_cores}', **params)
        else:
            subprocess.run(fr'swanrun.bat {self._config_name}', **params)

        if verbose:
            self._print_errors()

        os.chdir(current_folder)

    def _clean_output(self):
        files_to_clean = [f'{self._config_name}.erf',
                          f'{self._config_name}.prt',
                          'Errfile', 'INPUT', 'PRINT', 'norm_end']
        for file_name in files_to_clean:
            if os.path.exists(file_name):
                os.remove(file_name)

    def _print_errors(self):
        files_to_analyze = [f'{self._config_name}.erf',
                            'Errfile']
        for file_name in files_to_analyze:
            if os.path.exists(file_name):
                with open(file_name, 'r') as file:
                    print(file_name)
                    print(file.read())

    def to_netcdf(self):
        if self._config:
            for var in ['HSig', 'RTP', 'PDIR']:
                output_file_name = self._config.get_output_label(var)

                output_to_netcdf(f'./results/{output_file_name}.dat',
                                 f'./results/{output_file_name}.nc',
                                 self._config)
        else:
            raise NotImplementedError('Output analysis for the custom config')
