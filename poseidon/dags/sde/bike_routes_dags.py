"""_dags file for 'bike routes' sde extraction."""
from airflow.models import DAG
from trident.util import general
from dags.sde.bike_routes_jobs import sde_to_shp
from trident.util.sde_extract_tasks import create_sde_tasks


args = general.args
conf = general.config
schedule = general.schedule['gis_weekly']
start_date = general.start_date['gis_weekly']
folder = 'bike_route'
layer = 'bike_routes'
datasd_name = 'bike_routes_datasd'
md = 'bike-route-lines'
path_to_file = conf['prod_data_dir'] + '/' + datasd_name

dag = DAG(dag_id='gis_{layer}'.format(layer=layer),
          default_args=args,
          start_date=start_date,
          schedule_interval=schedule)


#: Create tasks dynamically
create_sde_tasks(
    dag=dag,
    folder=folder,
    layer=layer,
    datasd_name=datasd_name,
    md=md,
    path_to_file=path_to_file,
    sde_to_shp=sde_to_shp)
