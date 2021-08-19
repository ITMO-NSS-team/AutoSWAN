import os

from core.utils.files import get_project_root


def _process_local_path(path):
    # TODO implement universal solution
    #if path[0] == '.':
    #    path = f'{get_project_root()}/{path[2:]}'
    path=path.replace('\\','/')
    for disk in ['C', 'D', 'E', 'F', 'Z']:
        path = path.replace(f'{disk}:/', f'/mnt/{disk.lower()}/')
    return path


def interpolate_to_grid(grid_path: str, source_path: str, target_path: str, nearest=False):
    method = 'remapbil'
    if nearest:
        method = 'remapnn'
    print('WSL start')
    os.system('wsl export REMAP_EXTRAPOLATE=on')
    print(os.system(f'wsl cdo -P 4 {method},{grid_path} '
                    f'{_process_local_path(source_path)} '
                    f'{_process_local_path(target_path)}'))


def grb2_to_nc(grid_path: str, nc_path: str):
    print(os.system(f'wsl cdo -f nc copy '
                    f'{_process_local_path(grid_path)} '
                    f'{_process_local_path(nc_path)}'))


def merge_time(template_to_merge: str, final_path: str):
    if os.path.exists(f'{_process_local_path(final_path)}'):
        # remove unnecessary grb file
        os.remove(f'{_process_local_path(final_path)}')
    print(os.system(f'wsl cdo mergetime {_process_local_path(template_to_merge)} {_process_local_path(final_path)}'))


def subset_vars(file_name_in: str, file_name_out: str, expr: str):
    if os.path.exists(f'{_process_local_path(file_name_out)}'):
        # remove unnecessary grb file
        os.remove(f'{_process_local_path(file_name_out)}')

    print(os.system(
        f"wsl cdo expr,'{expr}' "
        f" {_process_local_path(file_name_in)} {_process_local_path(file_name_out)}"))


def split_grib2(file_name: str):
    print(os.system(f'wsl grib_copy {_process_local_path(file_name)} '
                    f'{_process_local_path(file_name)}_[typeOfLevel].grib2'))
