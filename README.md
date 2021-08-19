## Brief description

This repository contains the toolbox for the automated creation of the [SWAN](http://swanmodel.sourceforge.net/) wind wave model configurations for the local domains.

## How to run:

To run the SWAN simulation for the new domain:

```python
from core.simulation_case.case import Case
case = Case('domain_description.json')
case.prepare_case()
case.run()
```

The output is automatically converting to NetCDF4 format.

## Configure new case

1. Create JSON the describes the configuration (see the examples in 'cases' folder)
2. Set the coordinates and paths to the data. The possible values of the BDC sources can be seen [here](https://polar.ncep.noaa.gov/waves/hindcasts/prod-multi_1.php). By default, the global wave reanalysis from NOAA is used.
3. The source of bathymetry data can be obtained from [GEBCO](https://www.gebco.net/).

### Example of configuration structure:

```json
{
  "id": "pacific_example",
  "case_description": {
    "area_name": "Bering Sea",
    "coords": "[(53.0, 159), (53.0, 162.0), (54.0, 162), (54.0, 159.0)]",
    "grid": {
      "step": 500,
      "step_unit": "m",
      "grid_type": "deg"
    },
    "open_boundaries": "['N','S','W','E']"
  },
  "simulation": {
    "spinup_start": "2021-01-01 00:00",
    "start": "2021-01-05 00:00",
    "end": "2021-01-10 23:00",
    "integration_step": "10 MIN",
    "parallel": "False",
    "model": "SWAN4131"
  },
  "data": {
    "upload_data": "True",
    "storage_path": "./storage",
    "force_overwrite": "False",
    "bathy_source": "./data/gebco_small.nc",
    "bdc_ncep_dataset_type": "ak_10m",
    "wind_dataset_type": "cfs2"
  },
  "output": {
    "variables": "['HSig','PDIR','RTP']",
    "save_output_fields": "True",
    "save_spectres": "True",
    "points": {
      "P1": "(53.5, 159.8, 'First point')",
      "P2": "(53.2, 159.9, 'Second point')"
    }
  },
  "nesting": {
    "nested_grid": "None"
  }
}
```

## Installation

CDO toolbox installation (Win10):

1. Install Windows Subsystem for Linux (as admin):
```
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

2. Install Ubuntu Linux from Microsoft Store, restart the PC.

3. Install [CDO](https://code.mpimet.mpg.de/projects/cdo/) package as:
```
ubuntu
sudo apt-get update
sudo apt-get install -y cdo
```

4. Fix Qt5/WSL1 issue with:
```
sudo strip --remove-section=.note.ABI-tag /usr/lib/x86_64-linux-gnu/libQt5Core.so.5
```

5. (optional) If you want to upload the ERA5 wind data in automated way, use the [instruction](https://cds.climate.copernicus.eu/api-how-to) 
to obtain the CDS API key and pun it to the $HOME/.cdsapirc.

6. (optional) To run the SWAN in parallel mode - install MPICH2 for [Windows](http://swanmodel.sourceforge.net/online_doc/swanimp/node10.html).