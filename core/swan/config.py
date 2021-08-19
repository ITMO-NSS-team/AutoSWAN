from dataclasses import dataclass

from core.domain.grid import Grid
from core.domain.task import SimulationTask
from core.simulation_case.case_options import OutputOptions
from core.swan.utils import format_datetime


@dataclass
class SwanConfig:
    wind_step: str
    wind_drag: float
    int_step: str
    grid: Grid
    task: SimulationTask
    output_options: OutputOptions

    @property
    def grid_desc(self):
        return self._grid_to_description(self.grid.grid_type)

    @property
    def input_grid(self):
        return self._grid_to_input_desciption(self.grid.grid_type)

    @property
    def output_width(self):
        return self.grid.x_cells

    @property
    def coordinates_type(self):
        return self.grid.grid_type

    @property
    def bdc(self):
        return self._get_bdc_description()

    @property
    def wind_start(self):
        return format_datetime(self.task.spinup_start)

    @property
    def wind_end(self):
        return format_datetime(self.task.simulation_end)

    @property
    def start_datetime(self):
        return format_datetime(self.task.simulation_start)

    @property
    def end_datetime(self):
        return format_datetime(self.task.simulation_end)

    def get_output_label(self, variable_name):
        return f'{variable_name}_{self.config_label}'

    @property
    def config_label(self):
        return f'{self.grid.grid_id}_' \
               f'{format_datetime(self.task.simulation_start)}_' \
               f'{format_datetime(self.task.simulation_end)}'

    @staticmethod
    def generate(task: SimulationTask, grid: Grid, output_options: OutputOptions):
        wind_step = '1 HR'  # TODO automate
        wind_drag = 1.21
        int_step = task.integration_step  # TODO automate

        config = SwanConfig(wind_step, wind_drag, int_step, grid, task, output_options=output_options)

        return config

    def fill_template(self, template: str):
        return template.format(coordinates_type=self.coordinates_type,
                               grid_desc=self.grid_desc,
                               input_grid=self.input_grid,
                               output_width=self.output_width,
                               wind_start=self.wind_start,
                               wind_step=self.wind_step,
                               wind_end=self.wind_end,
                               wind_drag=self.wind_drag,
                               bdc=self.bdc,
                               start_datetime=self.start_datetime,
                               int_step=self.int_step,
                               end_datetime=self.end_datetime,
                               model_params=self._get_model_params(),
                               fields_output=self._get_output_field_description(),
                               points_output=self._get_output_points_description(),
                               spectral_output=self._get_spectre_description()
                               )

    def _get_output_points_description(self):
        pt_descr = ''
        if self.output_options.target_points is not None:
            for pt in self.output_options.target_points:
                pt_descr += f"POINTS '{pt.name}' {pt.lon} {pt.lat} ${pt.description}\n"

            pt_descr += '\n'

            for pt in self.output_options.target_points:
                pt_descr += f"TABLE '{pt.name}' HEAD 'results\\{pt.name}_{self.config_label}.tab' & \n" \
                            f"TIME DEPth HSign DIR WLEN PDIR TDIR TM01 RTP TM02 TMM10 PER WIND &\n" \
                            f"OUTPUT {self.start_datetime} 1 HR\n"
        return pt_descr

    def _get_model_params(self):
        if self.task.model == 'SWAN4072':
            phys_params = f"GEN3 KOMEN 2.36e-5 3.02e-3 \n" \
                          "BREAKING\n" \
                          "FRiction JONswap CONstant 0.067\n" \
                          "TRIAD\n" \
                          "DIFFRACtion\n" \
                          "PROP BSBT\n"
        elif self.task.model == 'SWAN4131' or self.task.model == 'SWAN4120A':
            phys_params = f"GEN3 ST6 6.5E-6 8.5E-5 4.0 4.0 UP HWANG VECTAU U10PROXY 35.0 AGROW \n" \
                          "BREAKING\n" \
                          "FRiction JONswap CONstant 0.067\n" \
                          "TRIAD\n" \
                          "DIFFRACtion\n " \
                          "PROP BSBT\n" \
                          "QUANTity  Per short='Tm-1,0' power=0.\n"
        else:
            raise ValueError(f'Physical params not found for {self.task.model} model.')
        return phys_params

    def _get_output_field_description(self):
        out_descr_full = ''
        if self.output_options.is_save_output_fields and self.output_options.variables is not None:
            for var in self.output_options.variables:
                out_descr_full += f"BLOCK 'COMPGRID' NOHEAD 'results\\{self.get_output_label(var)}.dat' " \
                                  f"LAYOUT 1 {var} OUT {self.start_datetime} 1. HR\n"
        return out_descr_full

    def _get_spectre_description(self):
        out_descr_full = ''
        if self.output_options.is_save_output_fields and self.output_options.variables is not None:
            for pt in self.output_options.target_points:
                out_descr_full += f"SPECout '{pt.name}' SPEC2D ABS 'results\\{pt.name}_{self.config_label}.spc' & \n" \
                                  f"OUTPUT {self.start_datetime} 1 HR\n"
        return out_descr_full

    def _grid_to_description(self, grid_type: str):
        if grid_type == 'spherical':
            return (f"""CGRID REGular xpc={self.grid.min_x}  ypc={self.grid.min_y} alpc=0. &
                  xlenc={self.grid.x_len} ylenc={self.grid.y_len} mxc={self.grid.x_cells - 1} myc={self.grid.y_cells - 1} &
                  CIRCLE mdc=36 flow=0.05 fhigh=1. msc=25""")
        elif grid_type == 'CART':
            return (
                f"""CGRID REGular 0. 0. 0. {self.grid.x_len} {self.grid.y_len} {self.grid.x_cells - 1} {self.grid.y_cells - 1} CIRCLE 36 0.05 1.0 41""")
        else:
            raise NotImplementedError('Grid type should be SPHerical or CARTestian')

    def _grid_to_input_desciption(self, grid_type: str):
        if grid_type == 'spherical':
            return (f"""REGular xpinp={self.grid.min_x}  ypinp={self.grid.min_y} & 
                alpinp=0. mxinp={self.grid.x_cells - 1} myinp={self.grid.y_cells - 1} &
                dxinp={round(self.grid.x_step_deg, 6)} dyinp={round(self.grid.y_step_deg, 6)}""")
        elif grid_type == 'CART':
            return (
                f"""0. 0. 0. {self.grid.x_cells - 1} {self.grid.y_cells - 1} {self.grid.step} {self.grid.step}""")
        else:
            raise NotImplementedError('Grid type should be SPHerical or CARTestian')

    def _get_bdc_description(self):
        if not self.grid.open_boundaries or not self.grid.bdc_description:
            return ''
        bdc_descr = ''

        for bdc_description in self.grid.bdc_description:
            i0, j0, i1, j1, bdc_filepath = bdc_description
            bdc_length = round((self.grid.x_len / self.grid.x_cells) * (abs(i0 - i1) + abs(j0 - j1)), 6)
            bdc_descr += f"BOUndspec SEGMent IJ  {i0}  {j0} {i1} {j1} VARiable FILE {bdc_length} '{bdc_filepath}'\n"

        return bdc_descr
