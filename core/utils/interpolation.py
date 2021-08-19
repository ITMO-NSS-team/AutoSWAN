from core.utils.cdo import interpolate_to_grid

_interpolation_mode = 'cdo'


def interpolate_data_to_grid(grid: 'Grid', source_path: str, target_path: str, ):
    if not grid.instance_path:
        raise ValueError('Grid instance not exists')

    if _interpolation_mode == 'cdo':
        interpolate_to_grid(grid.instance_path, source_path, target_path, nearest=False)
    else:
        raise NotImplementedError('Interpolation mode not supported')
