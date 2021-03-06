"""_jobs file for 'streets alleys walkways' layer sde extraction."""
from trident.util import general
from trident.util import geospatial
import pandas as pd
from collections import OrderedDict
import logging

conf = general.config
table = 'STREET_ALLEY_WALKWAY'
prod_dir = conf['prod_data_dir']
layername = 'sd_paving_segs_datasd'
layer = prod_dir + '/' + layername

dtypes = OrderedDict([
        ('objectid', 'int:9'),
        ('roadsegid', 'int:10'),
        ('sapid', 'str:9'),
        ('road20full','str:23'),
        ('xstrt1','str:23'),
        ('xstrt2','str:23'),
        ('llowaddr','int:10'),
        ('lhighaddr','int:10'),
        ('rlowaddr','int:10'),
        ('rhighaddr','int:10'),
        ('zip','int:10'),
    ])

gtype = 'LineString'


def sde_to_shp():
    """SDE table to Shapefile."""
    logging.info('Extracting {layername} layer from SDE.'.format(
        layername=layername))
    df = geospatial.extract_sde_data(table=table
                                     #where="OWNERSHIP = 'City of San Diego'"
                                     )

    logging.info('Processing {layername} df.'.format(layername=layername))

    
    logging.info(df.head())

    logging.info('Converting {layername} df to shapefile.'.format(
        layername=layername))
    geospatial.df2shp(df=df,
                      folder=prod_dir,
                      layername=layername,
                      dtypes=dtypes,
                      gtype=gtype,
                      epsg=2230)
    return 'Successfully converted {layername} to shapefile.'.format(
           layername=layername)
