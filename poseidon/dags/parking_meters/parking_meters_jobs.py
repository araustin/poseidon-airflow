"""Parking meters _jobs file."""
import string
import os
import pandas as pd
import glob
import logging
from datetime import datetime, timedelta, date
from trident.util import general


conf = general.config
cur_yr = general.get_year()
cur_mon = datetime.now().month
portal_fname = conf['prod_data_dir'] +'/treas_parking_payments_{}_datasd_v1.csv'.format(cur_yr)

def ftp_download_wget():
 """Download parking meters data from FTP."""
 
 wget_str = "wget -np --continue " \
 + "--user=$ftp_user " \
 + "--password='$ftp_pass' " \
 + "--directory-prefix=$temp_dir " \
 + "ftp://ftp.datasd.org/uploads/IPS/SanDiegoData_{0}{1}*.csv".format(cur_yr, cur_mon)
 tmpl = string.Template(wget_str)
 command = tmpl.substitute(
 ftp_user=conf['ftp_datasd_user'],
 ftp_pass=conf['ftp_datasd_pass'],
 temp_dir=conf['temp_data_dir'])
 
 return command

def build_prod_file(**kwargs):
    """Process parking meters data."""

    # Look for files for the past week
    # Job dies sometimes with more files
    last_week = (datetime.now() - timedelta(days=6)).day
    today = datetime.now().day
    logging.info(last_week)
    
    if last_week > today:
        day_from = 1
    else:
        day_from = last_week

    list_ = []

    for day in range(day_from,today+1):
        filename = conf['temp_data_dir'] + "/SanDiegoData_{0}{1}{2}*.csv".format(cur_yr, cur_mon, day)
        logging.info("Looking for a file for "+str(day))
        files = glob.glob(filename)
        frame = pd.DataFrame()
        for file_ in files:
            try:
                df = pd.read_csv(file_, index_col=False, header=0)
                list_.append(df)
                logging.info("Read "+file_)
            except:
                logging.info(str(file_) + " is empty or broken") 
    
    frame = pd.concat(list_, ignore_index=True)

    # Clean the schema
    logging.info("Cleaning the schema")
    update = frame[['MeterType', 'PoleSerNo', 'Amount',
                    'TransactionType', 'StartDateTime', 'ExpiryTime']]

    update = update.rename(columns={
        'MeterType': 'meter_type',
        'StartDateTime': 'date_trans_start',
        'ExpiryTime': 'date_meter_expire',
        'Amount': 'trans_amt',
        'TransactionType': 'pay_method',
        'StartDateTime': 'date_trans_start',
        'PoleSerNo': 'pole_id'
    })

    # Convert datetime columns to dt
    logging.info("Setting datetime for update file")
    update['date_trans_start'] = pd.to_datetime(update['date_trans_start'],
                                           format="%m/%d/%Y %I:%M:%S %p",
                                           errors='coerce')

    update['date_meter_expire'] = pd.to_datetime(update['date_meter_expire'],
                                            format="%m/%d/%Y %I:%M:%S %p",
                                            errors='coerce')

    # Convert transactions to cents.
    logging.info("Converting update transactions to cents")
    update['trans_amt'] = update['trans_amt'] * 100
    update['trans_amt'] = update['trans_amt'].astype(int)

    # Standardize fields
    logging.info("Standardizing update fields")
    update.meter_type = update.meter_type.str.upper()
    update.pole_id = update.pole_id.str.upper()
    update.pay_method = update.pay_method.str.upper()
    update.meter_type = update.meter_type.str.extract('(SS|MS)', expand=False)

    # Construct a unique id:
    logging.info("Generating UUID for update file")
    update['uuid'] = update.meter_type.str.cat(update.pole_id, sep="")\
        .str.cat(update.date_trans_start.dt.strftime('%y%m%d%H%M%S'), sep="")\
        .str.cat(update.trans_amt.astype(str), sep="")\
        .str.replace("-", "")
    
    # Rearrange column order
    logging.info("Rearranging column order")
    cols = update.columns.tolist()
    # Set last column as first
    cols = cols[-1:] + cols[:-1]
    update = update[cols]

    logging.info("Sorting by transaction start")
    update = update.sort_values(by='date_trans_start')

    logging.info("Removing entries from other years")
    update = update[update['date_trans_start'] >= cur_yr+'-01-01 00:00:00']

    # Look for an existing file for the year to add to
    logging.info("Looking for this year's file")

    if os.path.isfile(portal_fname):
        logging.info("Found this year's file")
        portal = pd.read_csv(portal_fname)
        logging.info("Concatenating update + portal")
        portal_up = pd.concat([portal, update])

    else:
        logging.info("Did not find this year's file")
        logging.info("Starting a new file for this year")
        portal_up = update
        

    # Original update number of entries
    orig_entries_ct = portal_up.shape[0]

    # Drop duplicate entries
    logging.info("Dropping duplicates")
    portal_up_dedupe = portal_up.drop_duplicates('uuid', keep='last')

    # Log amt of duplicates found
    logging.info(
        'Found and removed ' +
        str(orig_entries_ct - portal_up_dedupe.shape[0]) +
        ' duplicated entries out of ' +
        str(orig_entries_ct)
        )

    logging.info("Writing updated data to " + portal_fname)
    general.pos_write_csv(
        portal_up_dedupe,
        portal_fname,
        date_format=conf['date_format_ymd_hms'])  

    return "Updated prod file"


def build_aggregation(agg_type="pole_by_month", **kwargs):
    """Aggregate raw production data by month/day."""
    out_fname = 'treas_meters_{0}_{1}_datasd_v1.csv'.format(cur_yr,agg_type)

    logging.info("Reading portal data " + portal_fname)
    portal = pd.read_csv(portal_fname)

    logging.info("Translate start_date to dt, create agg columns")

    portal['date_trans_start'] = pd.to_datetime(
                                portal['date_trans_start'],
                                format="%Y-%m-%d %H:%M:%S",
                                errors='coerce')
    portal['month'] = portal.date_trans_start.dt.month
    portal['day'] = portal.date_trans_start.dt.day

    logging.info("Creating " + agg_type + " aggregation")
    if agg_type == 'pole_by_month':
        grouped = portal.groupby(['pole_id', 'month'],
                                 as_index=False)

        aggregation = grouped['trans_amt'].agg({
                                                'sum_trans_amt': 'sum',
                                                'num_trans': 'count'
                                              })
    elif agg_type == 'pole_by_mo_day':
        grouped = portal.groupby(['pole_id', 'month', 'day'],
                                 as_index=False)

        aggregation = grouped['trans_amt'].agg({
                                                'sum_trans_amt': 'sum',
                                                'num_trans': 'count'
                                              })
    else:
        raise NotImplementedError("Not sure what " + agg_type + " is")

    new_file_path = '{0}/{1}'.format(conf['prod_data_dir'],out_fname)

    logging.info("Writing " + agg_type + " aggregation")
    general.pos_write_csv(
        aggregation,
        new_file_path,
        date_format=conf['date_format_ymd_hms'])

    return "Updated agg " + agg_type + " file " + new_file_path
