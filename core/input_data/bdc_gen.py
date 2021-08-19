import glob
import json
import os
from copy import copy
from typing import List

import netCDF4 as nc
import numpy as np
import pandas as pd

from core.domain.grid import Grid
from core.domain.task import SimulationTask
from core.swan.utils import format_datetime
from core.utils.date import month_range
from core.utils.geo import coords_with_data, get_nearest_index
from core.utils.netcdf import get_data_var, time_from_netcdf

sides = ['W', 'N', 'S', 'E']


def create_bdc(domain_name: str, grid: Grid, task: SimulationTask,
               bathy_path: str,
               initial_bdc_template: str,
               output_path: str,
               use_cached=True):
    grid.save_as_cdo_grid('./data/grid')

    if glob.glob('./data/*.tpar'):
        return

    bathy_source = nc.Dataset(bathy_path, 'r', format='NETCDF4')

    try:
        bdc_file_name = initial_bdc_template.format(date=format_datetime(task.spinup_start, monthly=True), var='hs')
    except:
        bdc_file_name = initial_bdc_template.format(date=format_datetime(task.spinup_start, monthly=True),
                                                    year=task.spinup_start.year)

    bdc_source = nc.Dataset(bdc_file_name, 'r', format='NETCDF4')

    description = []
    if grid.open_boundaries:
        for side in grid.open_boundaries:
            cached_bdc_info_file_name = f'./data/bdc_info_{grid.grid_id}_{side}.json'

            if not os.path.exists(cached_bdc_info_file_name) or not use_cached:
                bdc_names, bdc_coords, bdc_source_coords = _bdc_for_side(side_id=side, bdc_source=bdc_source,
                                                                         bathy_source=bathy_source)

                full_bdc_info = {'bdc_names': bdc_names,
                                 'out_grid_coords': bdc_coords,
                                 'out_coords': bdc_source_coords}
                with open(cached_bdc_info_file_name, 'w') as outfile:
                    json.dump(full_bdc_info, outfile)

            else:
                with open(cached_bdc_info_file_name, 'r') as infile:
                    full_bdc_info_json = json.load(infile)
                bdc_names = full_bdc_info_json['bdc_names']
                bdc_coords = full_bdc_info_json['out_grid_coords']
                bdc_source_coords = full_bdc_info_json['out_coords']

            _bdc_to_txt(initial_bdc_template, output_path, bdc_names, bdc_source_coords, task)

            for i in range(0, len(bdc_names)):
                file_name = output_path.format(idx=bdc_names[i])
                coords = bdc_coords[i][0], bdc_coords[i][1]

                i0, j0, i1, j1 = 0, 0, 0, 0

                if side == 'N':
                    j0, j1 = grid.y_cells - 1, grid.y_cells - 1
                    i0, i1 = coords
                if side == 'S':
                    j0, j1 = 0, 0
                    i0, i1 = coords
                if side == 'E':
                    i0, i1 = grid.x_cells - 1, grid.x_cells - 1
                    j0, j1 = coords
                if side == 'W':
                    i0, i1 = 0, 0
                    j0, j1 = coords
                description.append((i0, j0, i1, j1, file_name))

    return description


def _bdc_for_side(side_id: str, bdc_source, bathy_source):
    prev_coords = None

    out_names = []
    out_coords = []
    out_grid_coords = []

    # TODO check is reverce needed
    bathy = np.asarray(bathy_source['elevation'])

    min_depth = 0.01

    if side_id == 'N':
        border_length = bathy.shape[1]
        border_mask = bathy[0, :] > min_depth
    elif side_id == 'S':
        border_length = bathy.shape[1]
        border_mask = bathy[-1, :] > min_depth
    elif side_id == 'W':
        border_length = bathy.shape[0]
        border_mask = np.flip(bathy[:, 0] > min_depth)
    elif side_id == 'E':
        border_length = bathy.shape[0]
        border_mask = np.flip(bathy[:, -1] > min_depth)
    else:
        raise NotImplementedError('Unknown side')

    bdc_start = 0
    bdc_end = 0
    bdc_ind = 1

    min_ind_x = 0
    min_ind_y = 0

    try:
        bdc_lon = bdc_source['lon']
        bdc_lat = bdc_source['lat']

    except IndexError:
        try:
            bdc_lon = bdc_source['nav_lon']
            bdc_lat = bdc_source['nav_lat']
        except IndexError:
            bdc_lon = bdc_source['longitude']
            bdc_lat = bdc_source['latitude']

    bdc_var_name = list(bdc_source.variables.keys())[-1]
    bdc = bdc_source[bdc_var_name]

    domain_lon = bathy_source['lon']
    domain_lat = bathy_source['lat']

    bdc_data_coords = coords_with_data(bdc_lon, bdc_lat, bdc)

    is_2d_grid = len(domain_lon.shape) > 1

    is_first_bdc_cell = True

    for i in range(border_length):
        if border_mask[i]:
            if side_id == 'N':
                if is_2d_grid:
                    bnd_pt_lon = ((360 + domain_lon[domain_lon.shape[0] - 1][i]) % 360)
                    bnd_pt_lat = domain_lat[domain_lon.shape[0] - 1][i]
                else:
                    bnd_pt_lon = ((360 + domain_lon[i]) % 360)
                    bnd_pt_lat = domain_lat[domain_lon.shape[0] - 1]
            elif side_id == 'S':
                if is_2d_grid:
                    bnd_pt_lon = ((360 + domain_lon[0][i]) % 360)
                    bnd_pt_lat = domain_lat[0][i]
                else:
                    bnd_pt_lon = ((360 + domain_lon[i]) % 360)
                    bnd_pt_lat = domain_lat[0]
            elif side_id == 'E':
                if is_2d_grid:
                    bnd_pt_lon = ((360 + domain_lon[i][domain_lon.shape[1] - 1]) % 360)
                    bnd_pt_lat = domain_lat[i][domain_lon.shape[1] - 1]
                else:
                    bnd_pt_lon = ((360 + domain_lon[domain_lon.shape[1] - 1]) % 360)
                    bnd_pt_lat = domain_lat[i]
            elif side_id == 'W':
                if is_2d_grid:
                    bnd_pt_lon = ((360 + domain_lon[i][0]) % 360)
                    bnd_pt_lat = domain_lat[i][0]
                else:
                    bnd_pt_lon = ((360 + domain_lon[0]) % 360)
                    bnd_pt_lat = domain_lat[i]
            else:
                raise NotImplementedError(f'Unknown side {side_id}')
            min_ind_x, min_ind_y = get_nearest_index(bdc_data_coords, bnd_pt_lon, bnd_pt_lat)
            new_coords = (min_ind_x, min_ind_y)

            if not prev_coords:
                prev_coords = copy(new_coords)

            land_starts_cond = border_mask[i] and (i + 1 < border_length and not border_mask[i + 1])
            border_ends_cond = (i == border_length - 1)

            if is_first_bdc_cell:
                bdc_start = i
                is_first_bdc_cell = False
            else:
                bdc_end = i

            if (not np.all(new_coords == prev_coords)) or \
                    border_ends_cond or land_starts_cond:
                bdc_ind = bdc_ind + 1
                print(side_id, bdc_ind, bdc_start, bdc_end, prev_coords)
                out_grid_coords.append((bdc_start, bdc_end))
                out_name = f'{side_id}_{bdc_start}_{bdc_end}'
                out_names.append(out_name)
                out_coords.append(prev_coords)

                bdc_start = i

            prev_coords = copy(new_coords)
        else:
            is_first_bdc_cell = True

    return out_names, out_grid_coords, out_coords


def _bdc_to_txt(input_bdc_template: str,
                final_file_name_template: str,
                out_names: List[str], bdc_source_coords,
                task: SimulationTask):
    df_res_full = None

    for bdc_ind in range(len(out_names)):
        is_first_year = True

        out_name = out_names[bdc_ind]
        x = bdc_source_coords[bdc_ind][0]
        y = bdc_source_coords[bdc_ind][1]
        for year in range(task.spinup_start.year, task.simulation_end.year + 1, 1):
            start_month, end_month = month_range(year, task)
            for mon in range(start_month, end_month + 1):
                date_lbl = f'{year}{mon:02d}'  # final_file_name_template.format(date=f'{year}{mon:02d}')

                try:
                    # ww3 case
                    file_name = input_bdc_template.format(date=date_lbl, year=year)
                    nc_file = nc.Dataset(file_name, 'r', format='NETCDF4')
                    hs_data = nc_file['hs']
                    direction = nc_file['dir']
                    period = 1 / np.asarray(nc_file['fp'])
                    raw_time = nc_file.variables['time']
                except Exception:
                    try:
                        # era5 case
                        file_name = input_bdc_template.format(date=date_lbl)
                        nc_file = nc.Dataset(file_name, 'r', format='NETCDF4')
                        hs_data = nc_file['swh']
                        direction = nc_file['mwd']
                        period = np.asarray(nc_file['pp1d'])
                        raw_time = nc_file.variables['time']
                    except Exception:
                        file_name = input_bdc_template.format(date=date_lbl, var='hs')

                        hs_file = nc.Dataset(file_name, 'r', format='NETCDF4')
                        hs_data = get_data_var(hs_file)

                        file_name = input_bdc_template.format(date=date_lbl, var='dp')
                        direction_file = nc.Dataset(file_name, 'r', format='NETCDF4')
                        direction = get_data_var(direction_file)

                        file_name = input_bdc_template.format(date=date_lbl, var='tp')
                        tp_file = nc.Dataset(file_name, 'r', format='NETCDF4')
                        period = get_data_var(tp_file)

                        raw_time = hs_file.variables['time']
                    # hs_file.close()
                    # direction_file.close()
                    # tp_file.close()
                dates = time_from_netcdf(raw_time)
                # nc_file.close()

                hs_list = hs_data[:, x, y]
                dir_list = ((direction[:, x, y]) + 360) % 360
                period_list = period[:, x, y]

                df_res = pd.DataFrame(
                    {'date': dates,
                     'hs': hs_list,
                     'period': period_list,
                     'peakdir': dir_list,
                     'dirspread': 30}
                )

                # save only bdc in spinup and simulation time range
                df_res = \
                    df_res.loc[(df_res['date'] >= task.spinup_start) & (df_res['date'] <= task.simulation_end)]

                df_res['date'] = [format_datetime(_) for _ in df_res['date']]

                df_res['hs'] = [f'{round(_, 2)}' for _ in df_res['hs']]
                df_res['period'] = [f'{round(_, 2)}' for _ in df_res['period']]
                df_res['peakdir'] = [f'{round(_, 0)}' for _ in df_res['peakdir']]
                df_res['dirspread'] = [f'{round(_, 0)}' for _ in df_res['dirspread']]

                if is_first_year:
                    df_res_full = copy(df_res)
                else:
                    df_res_full = df_res_full.append(df_res)

                is_first_year = False

        final_file_name = final_file_name_template.format(idx=out_name)

        # TODO fix not working
        # df_res_full.style.format(
        #    {'hs': '{:4.2f}',
        #     'period': '{:5.2f}',
        #     'peakdir': '{:3.0f}',
        #     'dirspread': '{:3.0f}'}
        # )

        with open(final_file_name, mode='w') as fin_file:
            fin_file.write('TPAR\n')
            # fin_file.write('\n')
        df_res_full.to_csv(final_file_name, sep=' ', index=False, header=False, mode='a')


def _month_range(year: int, task: SimulationTask):
    start_month = 1
    end_month = 12
    if year == task.simulation_start.year:
        start_month = task.simulation_start.month
    if year == task.simulation_end.year:
        end_month = task.simulation_end.month
    return start_month, end_month
