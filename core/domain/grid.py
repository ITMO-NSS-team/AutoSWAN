from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from core.utils.geo import distance
from core.utils.netcdf import get_dims, variable_to_netcdf


# Cartesian
# CGRID  REGular 0. 0. 0. 15000.0 24750.0 40 66 CIRCLE 36 0.05 1.0 41

# SET NAUTical
# MODE NONSTationary
# COORDinates SPHErical

# CGRID REGular xpc=27.211625  ypc=40.772549 alpc=0. &
#      xlenc=15 ylenc=6.513 mxc=299 myc=129 &
#      CIRCLE mdc=36 flow=0.05 fhigh=1. msc=25

@dataclass
class Grid:
    grid_id: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    step: float
    step_y: Optional[float] = None
    step_type: str = 'm'
    instance_path: str = None
    grid_type: str = 'spherical'
    open_boundaries: List = None
    bdc_description: List = None

    @property
    def x_cells(self):
        if self.instance_path is not None and self.instance_path.endswith('.nc'):
            return get_dims(self.instance_path)[1]
        else:
            return int(round((self.max_x - self.min_x) / self.x_step_deg))

    @property
    def y_cells(self):
        if self.instance_path is not None and self.instance_path.endswith('.nc'):
            return get_dims(self.instance_path)[0]
        else:
            return int(round((self.max_y - self.min_y) / self.y_step_deg))

    @property
    def y_step_deg(self):
        if self.step_type == 'm':
            if not self.step_y:
                return (self.step / 1000) / 110.54

            else:
                return (self.step_y / 1000) / 110.54

        else:
            if not self.step_y:
                return self.step
            else:
                return self.step_y

    @property
    def x_step_deg(self):
        if self.step_type == 'm':
            latitude = (self.max_y + self.min_y) / 2
            return (self.step / 1000) / (111.320 * np.cos(latitude / 180 * np.pi))
        else:
            return self.step

    @property
    def x_len(self):
        if self.grid_type == 'spherical':
            return round(self.max_x - self.min_x, 6)
        elif self.grid_type == 'CART':
            return (self.x_cells - 1) * self.step

    @property
    def y_len(self):
        if self.grid_type == 'spherical':
            return round(self.max_y - self.min_y, 6)
        elif self.grid_type == 'CART':
            return (self.y_cells - 1) * self.step_y

    def save_as_cdo_grid(self, file_name: str):
        if not self.instance_path or not self.instance_path.endswith('.nc'):
            grid_description = (f"""gridtype = lonlat
    xsize = {self.x_cells}
    ysize = {self.y_cells} 
    xfirst = {self.min_x}
    xinc = {round(self.x_step_deg, 6)}
    yfirst = {self.min_y}
    yinc = {round(self.y_step_deg, 6)}
    """)

            with open(file_name, 'w') as text_file:
                text_file.write(grid_description)

            self.instance_path = file_name
        else:
            return


def grid_from_coords(grid_id: str, coords: List[Tuple[float, float]],
                     step: float, step_y=None, step_type: str = 'm',
                     grid_type='spherical'):
    min_x = min([lonlat[1] for lonlat in coords])
    min_y = min([lonlat[0] for lonlat in coords])

    max_x = max([lonlat[1] for lonlat in coords])
    max_y = max([lonlat[0] for lonlat in coords])

    grid = Grid(grid_id, min_x, min_y, max_x, max_y, step, step_y, step_type,
                grid_type=grid_type)

    return grid


def grid_from_txt(grid_id: str, grid_txt_path: str, grid_type='spherical', fixed_step: int = -1):
    """
    Generate grid from txt with non-regular grid with near-constant step in meters
    :param grid_id: grid id
    :param grid_txt_path: path to file with coords
    :return: Grid object
    """

    lats, lons = _parse_coords_from_txt_short(grid_txt_path)

    # TODO find mean step
    # step = round(distance(lats[0, 0], lons[0, 0], lats[1, 0], lons[1, 0]))

    x_lim = lats.shape[0] - 1
    y_lim = lats.shape[1] - 1

    if fixed_step > 0:
        # if the grid step in m is known
        step_x = fixed_step
        step_y = fixed_step
    else:
        step_x = round((distance(lats[0, 0], lons[0, 0], lats[x_lim, 0], lons[x_lim, 0])) / (x_lim + 1))

        step_y = round((distance(lats[0, 0], lons[0, 0], lats[0, y_lim], lons[0, y_lim])) / (y_lim + 1))

    step_type = 'm'

    instance_path = f'{grid_txt_path}.nc'
    variable_to_netcdf(lons, lats, 'mask', None, instance_path)

    grid = Grid(grid_id, min_x=np.min(lons), min_y=np.min(lats), max_x=np.max(lons), max_y=np.max(lats),
                step=step_x, step_y=step_y, step_type=step_type,
                instance_path=instance_path, grid_type=grid_type)
    return grid


def _parse_coords_from_txt(grid_txt_path: str):
    raw_coords = np.genfromtxt(grid_txt_path, delimiter='')

    lats = np.zeros(shape=(raw_coords.shape[0], int(raw_coords.shape[1] / 2)))
    lons = np.zeros(shape=(raw_coords.shape[0], int(raw_coords.shape[1] / 2)))

    for i in range(raw_coords.shape[0]):
        for j in range(raw_coords.shape[1]):
            if j % 2 == 0:
                lons[i, int(j / 2)] = raw_coords[i, j]
            else:
                lats[i, int(j / 2)] = raw_coords[i, j]

    return lats, lons


def _parse_coords_from_crd(grid_txt_path: str):
    with open(grid_txt_path) as f:
        lines = list(f)

    lats = np.zeros(shape=(int(len(lines)), int(len(lines[1].split()))))
    lons = np.zeros(shape=(int(len(lines)), int(len(lines[1].split()))))

    row_ind = 0
    for i in range(int(len(lines))):
        line = lines[i].split()
        if len(line) == 1:
            lats[row_ind, :] = line[0]
        else:
            for j in range(len(lines[1].split())):
                lons[row_ind, j] = float(line[j])
            row_ind = row_ind + 1

    return lats, lons


def _parse_coords_from_txt_short(grid_txt_path: str):
    with open(grid_txt_path) as f:
        lines = list(f)

    data_shape = (int(len(lines)), int(len(lines[1].split())) - 1)
    lons = np.zeros(shape=data_shape)
    lats = np.zeros(shape=data_shape)

    for row_ind in range(int(len(lines))):
        line = lines[row_ind].split()
        lats[row_ind,] = line[0]
        # else:
        # for j in range(len(lines[1].split())):
        lons[row_ind, :] = line[1:len(line)]

    return lats, lons
