from math import asin, cos, sqrt

import numpy as np


def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) * 1000


def distances_vectorized(lats, lons, lat1, lon1):
    p = 0.017453292519943295
    lats_arr = np.array(lats)
    lons_arr = np.array(lons)
    a = 0.5 - np.cos((lats_arr - lat1) * p) / 2 + np.cos(lat1 * p) * \
        np.cos(lats_arr * p) * (1 - np.cos((lons_arr - lon1) * p)) / 2
    return list(12742 * np.arcsin(np.sqrt(a)) * 1000)


def coords_with_data(bdy_lon_vec, bdy_lat_vec, bdy_data):
    coords = []

    if bdy_data.dimensions[-1] == 'time':
        i_range = range(bdy_data.shape[0])
        j_range = range(bdy_data.shape[1])
    else:
        i_range = range(bdy_data.shape[1])
        j_range = range(bdy_data.shape[2])

    for i in i_range:
        for j in j_range:
            if bdy_data.dimensions[-1] == 'time':
                data_cell = bdy_data[i, j, 0]
            else:
                data_cell = bdy_data[0, i, j]
            if data_cell is not np.ma.masked:
                if len(bdy_lat_vec.shape) > 1:
                    coords.append({'lat': bdy_lat_vec[i][j],
                                   'lon': bdy_lon_vec[i][j],
                                   'i': i,
                                   'j': j})
                else:
                    coords.append({'lat': bdy_lat_vec[i],
                                   'lon': bdy_lon_vec[j],
                                   'i': i,
                                   'j': j})
    return coords


def get_nearest_index(coords, pt_lon, pt_lat):
    # if len(pt_lon.shape)==1:
    #    res = min(coords, key=lambda p: distance(pt_lat, pt_lon, p['lat'], p['lon']))
    # else:
    dists = distances_vectorized([p['lat'] for p in coords],
                                 [p['lon'] for p in coords],
                                 pt_lat, pt_lon)

    try:
        res_ind = dists.index(min(dists))
    except:
        md = [min(_) for _ in dists]
        res_ind = md.index(min(md))
    min_ind_i, min_ind_j = coords[res_ind]['i'], coords[res_ind]['j']

    return min_ind_i, min_ind_j
