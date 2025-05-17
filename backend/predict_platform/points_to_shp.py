import logging

import numpy as np

from utils import points_to_shapefile
import os
from typing import Sequence, Dict


def number_2_hmc(coordinate_format_number):
    longitude = coordinate_format_number[0]
    latitude = coordinate_format_number[1]
    longitude_hour = int(longitude)
    longitude_ms = 60 * (longitude - longitude_hour)
    longitude_minute = int(longitude_ms)
    longitude_second = 60 * (longitude_ms - longitude_minute)
    latitude_hour = int(latitude)
    latitude_ms = 60 * (latitude - latitude_hour)
    latitude_minute = int(latitude_ms)
    latitude_second = 60 * (latitude_ms - latitude_minute)

    coordinate_format_hmc = {'longitude_hour': longitude_hour,
                             'longitude_minute': longitude_minute,
                             'longitude_second': longitude_second,
                             'latitude_hour': latitude_hour,
                             'latitude_minute': latitude_minute,
                             'latitude_second': latitude_second,
                             }
    return coordinate_format_hmc


def hmc_2_number(coordinate_format_hmc: Dict):
    longitude_hour = coordinate_format_hmc['longitude_hour']
    longitude_minute = coordinate_format_hmc['longitude_minute']
    longitude_second = coordinate_format_hmc['longitude_second']
    latitude_hour = coordinate_format_hmc['latitude_hour']
    latitude_minute = coordinate_format_hmc['latitude_minute']
    latitude_second = coordinate_format_hmc['latitude_second']

    longitude = (longitude_second / 60 + longitude_minute) / 60 + longitude_hour
    latitude = (latitude_second / 60 + latitude_minute) / 60 + latitude_hour
    coordinate_format_number = [longitude, latitude]
    return coordinate_format_number


def print_hmc(coordinate_format_hmc: Dict):
    longitude_hour = coordinate_format_hmc['longitude_hour']
    longitude_minute = coordinate_format_hmc['longitude_minute']
    longitude_second = coordinate_format_hmc['longitude_second']
    latitude_hour = coordinate_format_hmc['latitude_hour']
    latitude_minute = coordinate_format_hmc['latitude_minute']
    latitude_second = coordinate_format_hmc['latitude_second']

    if longitude_hour >= 0:
        hemisphere_sn = 'N'
    else:
        hemisphere_sn = 'S'

    if latitude_hour >= 0:
        hemisphere_ew = 'E'
    else:
        hemisphere_ew = 'W'
    logging.info(f"coordinates = {longitude_hour}\xb0{longitude_minute}'{longitude_second}''{hemisphere_sn}, {latitude_hour}\xb0{latitude_minute}'{latitude_second}''{hemisphere_ew}")


if __name__ == "__main__":
    output_shp_path = r'C:\Users\hp\Documents\ArcGIS\Projects\C_line\points'
    layer_name = 'points'
    geo_locations = [
                        # 109
                     {'longitude_hour': 122,
                      'longitude_minute': 27.9807,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 50.4035,
                      'latitude_second': 0
                      },
        # 110 # 111(1)
                     {'longitude_hour': 122,
                      'longitude_minute': 24.0027,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 47.1650,
                      'latitude_second': 0
                      },
        # 111(2)
                    {'longitude_hour': 122,
                     'longitude_minute': 23.4908,
                     'longitude_second': 0,
                     'latitude_hour': 33,
                     'latitude_minute': 46.9168,
                     'latitude_second': 0
                     },
        # 112(1)
                    {'longitude_hour': 122,
                     'longitude_minute': 21.0631,
                     'longitude_second': 0,
                     'latitude_hour': 33,
                     'latitude_minute': 45.6225,
                     'latitude_second': 0
                     },
        # 112(2) # 113(1)
                     {'longitude_hour': 122,
                      'longitude_minute': 19.0799,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 44.7799,
                      'latitude_second': 0
                      },
        # 113(2)
                     {'longitude_hour': 122,
                      'longitude_minute': 17.4773,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 44.2966,
                      'latitude_second': 0
                      },
        # 113(3)
                     {'longitude_hour': 122,
                      'longitude_minute': 16.9776,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 44.0528,
                      'latitude_second': 0
                      },
        # 114(1)
                     {'longitude_hour': 122,
                      'longitude_minute': 15.9648,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 43.6313,
                      'latitude_second': 0
                      },
        # 114(2)
                     {'longitude_hour': 122,
                      'longitude_minute': 14.9336,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 43.2471,
                      'latitude_second': 0
                      },
        # 116
                     {'longitude_hour': 122,
                      'longitude_minute': 9.9496,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 41.2997,
                      'latitude_second': 0
                      },
        # 117
                     {'longitude_hour': 122,
                      'longitude_minute': 7.7501,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 40.1796,
                      'latitude_second': 0
                      },
        # 118
                     {'longitude_hour': 122,
                      'longitude_minute': 5.9222,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 39.3999,
                      'latitude_second': 0
                      },
        # 119 # 120
                     {'longitude_hour': 122,
                      'longitude_minute': 3.7708,
                      'longitude_second': 0,
                      'latitude_hour': 33,
                      'latitude_minute': 38.1190,
                      'latitude_second': 0
                      },

        # 121
        {'longitude_hour': 122,
         'longitude_minute': 0.8988,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 35.7416,
         'latitude_second': 0
         },

        # 122
        {'longitude_hour': 122,
         'longitude_minute': 0.2054,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 35.3048,
         'latitude_second': 0
         },

        # 124(1)
        {'longitude_hour': 121,
         'longitude_minute': 56.9279,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 33.5607,
         'latitude_second': 0
         },
        # 124(2)
        {'longitude_hour': 121,
         'longitude_minute': 56.6796,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 33.3811,
         'latitude_second': 0
         },
        # 124(3)
        {'longitude_hour': 121,
         'longitude_minute': 56.4207,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 33.2233,
         'latitude_second': 0
         },

        # 125(1)
        {'longitude_hour': 121,
         'longitude_minute': 55.3706,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 32.6839,
         'latitude_second': 0
         },
        # 125(2)
        {'longitude_hour': 121,
         'longitude_minute': 55.0501,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 32.5402,
         'latitude_second': 0
         },

        # 128
        {'longitude_hour': 121,
         'longitude_minute': 51.2604,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 30.5976,
         'latitude_second': 0
         },

        # 129
        {'longitude_hour': 121,
         'longitude_minute': 50.3044,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 29.8577,
         'latitude_second': 0
         },

        # 131(1)
        {'longitude_hour': 121,
         'longitude_minute': 49.1064,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 28.9957,
         'latitude_second': 0
         },
        # 131(2)
        {'longitude_hour': 121,
         'longitude_minute': 48.8596,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 28.8562,
         'latitude_second': 0
         },
        # 131(3)
        {'longitude_hour': 121,
         'longitude_minute': 48.0124,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 28.5108,
         'latitude_second': 0
         },

        # 132(1)
        {'longitude_hour': 121,
         'longitude_minute': 47.4648,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 28.2649,
         'latitude_second': 0
         },
        # 132(2)
        {'longitude_hour': 121,
         'longitude_minute': 47.1771,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 28.1842,
         'latitude_second': 0
         },
        # 132(3)
        {'longitude_hour': 121,
         'longitude_minute': 46.6825,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 27.8849,
         'latitude_second': 0
         },

        # 133(1)
        {'longitude_hour': 121,
         'longitude_minute': 45.8000,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 27.4801,
         'latitude_second': 0
         },
        # 133(2)
        {'longitude_hour': 121,
         'longitude_minute': 45.5591,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 27.3687,
         'latitude_second': 0
         },
        # 133(3) 134(1)
        {'longitude_hour': 121,
         'longitude_minute': 45.2312,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 27.2541,
         'latitude_second': 0
         },

        # 134(2)
        {'longitude_hour': 121,
         'longitude_minute': 44.6780,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 26.9857,
         'latitude_second': 0
         },
        # 134(3)
        {'longitude_hour': 121,
         'longitude_minute': 44.3377,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 26.8178,
         'latitude_second': 0
         },
        # 134(4) 135(1)
        {'longitude_hour': 121,
         'longitude_minute': 43.6411,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 26.5508,
         'latitude_second': 0
         },

        # 135(2)
        {'longitude_hour': 121,
         'longitude_minute': 43.2356,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 26.3823,
         'latitude_second': 0
         },
        # 135(3)
        {'longitude_hour': 121,
         'longitude_minute': 42.9552,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 26.2490,
         'latitude_second': 0
         },

        # 136(1)
        {'longitude_hour': 121,
         'longitude_minute': 39.6837,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 24.8211,
         'latitude_second': 0
         },
        # 136(2)
        {'longitude_hour': 121,
         'longitude_minute': 39.2584,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 24.5491,
         'latitude_second': 0
         },

        # 137(1)
        {'longitude_hour': 121,
         'longitude_minute': 37.5596,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 23.5712,
         'latitude_second': 0
         },
        # 137(2) not exact
        {'longitude_hour': 121,
         'longitude_minute': 37.5210,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 23.5503,
         'latitude_second': 0
         },

        # 138
        {'longitude_hour': 121,
         'longitude_minute': 36.1069,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 22.7250,
         'latitude_second': 0
         },

        # 139
        {'longitude_hour': 121,
         'longitude_minute': 33.9059,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 21.7941,
         'latitude_second': 0
         },

        # 140(1)
        {'longitude_hour': 121,
         'longitude_minute': 32.9206,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 21.3376,
         'latitude_second': 0
         },
        # 140(2) 141(1)
        {'longitude_hour': 121,
         'longitude_minute': 32.7094,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 21.2257,
         'latitude_second': 0
         },

        # 141(2)
        {'longitude_hour': 121,
         'longitude_minute': 32.4609,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 21.1534,
         'latitude_second': 0
         },
        # 141(3)
        {'longitude_hour': 121,
         'longitude_minute': 32.2473,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 21.0467,
         'latitude_second': 0
         },
        # 141(4)
        {'longitude_hour': 121,
         'longitude_minute': 31.9384,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.9031,
         'latitude_second': 0
         },
        # 141(5)
        {'longitude_hour': 121,
         'longitude_minute': 31.7058,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.8527,
         'latitude_second': 0
         },

        # 142(1)
        {'longitude_hour': 121,
         'longitude_minute': 30.7115,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.5414,
         'latitude_second': 0
         },
        # 142(2)
        {'longitude_hour': 121,
         'longitude_minute': 30.4952,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.4765,
         'latitude_second': 0
         },
        # 142(3)
        {'longitude_hour': 121,
         'longitude_minute': 30.1546,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.3199,
         'latitude_second': 0
         },
        # 142(4)
        {'longitude_hour': 121,
         'longitude_minute': 30.0315,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 20.2702,
         'latitude_second': 0
         },
        # 142(5)
        {'longitude_hour': 121,
         'longitude_minute': 27.0223,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 19.0458,
         'latitude_second': 0
         },

        # 143c1(5)
        {'longitude_hour': 121,
         'longitude_minute': 25.1981,
         'longitude_second': 0,
         'latitude_hour': 33,
         'latitude_minute': 18.2960,
         'latitude_second': 0
         },
                     ]
    ids = np.arange(0, len(geo_locations))

    new_geo_locations = np.zeros((len(geo_locations), 2))
    for i, item in enumerate(geo_locations):
        new_geo_locations[i] = hmc_2_number(item)
    logging.info(np.reshape(ids, (-1, 1)))
    new_geo_locations = np.concatenate((np.reshape(ids, (-1, 1)), new_geo_locations), axis=1)
    logging.info(new_geo_locations)
    points_to_shapefile(layer_name, new_geo_locations, output_shp_path, 4326)

    pass