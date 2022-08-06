
import numpy as np, scipy, scipy.stats as stats, pandas as pd, matplotlib.pyplot as plt, seaborn as sns

import sqlalchemy

import paho.mqtt.client, paho.mqtt.publish

import tzlocal, pytz
import datetime, dateutil

import logging

engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5432/postgres')

def to_float(x):
    try:
        return float(x)
    except:
        return np.nan

def convert_on_off_to_true_and_false(x):
    if x in set(['on', 'ON', 'On', 'True', 'true']):
        return 1.0
    if x in set(['off', 'OFF', 'Off', 'False', 'false']):
        return 0.0
    if x in ['unavailable']:
        return np.nan
    raise Exception('Unknown value to convert in convert_on_off_to_true_and_false: ' + str(x))

def convert_to_time_slice_minutes_back_df(ldf1, time_slice_minutes_back):
    ldf1['last_updated'] = ldf1['last_updated'].dt.tz_convert(pytz.UTC).dt.tz_convert(tzlocal.get_localzone())
    ldf1 = ldf1[['last_updated', 'state']].set_index('last_updated')
    start_date = ldf1.loc[:time_slice_minutes_back, :].iloc[[-1]].index[0]
    ldf1 = ldf1.loc[start_date:]
    return ldf1


class FritzPowerPlug():

    ON_OFF_ENTITY_NAME = "switch.{device_name}"
    POWER_CONSUMPTION_ENTITY_NAME = "sensor.{device_name}_power_consumption"

    MQTT_TRIGGER_OFF_TOPIC = 'automation/{device_name}_trigger_off'

    def __init__(self, device_name, standby_limit_in_watt, time_slice_minutes_back=12, mqtt_auth = dict(username='mqttuser', password='mqttpasswd'), mqtt_hostname="odroid", mqtt_port=1883):
        self.device_name = device_name
        self.standby_limit_in_watt = standby_limit_in_watt
        self.mqtt_auth = mqtt_auth
        self.mqtt_hostname = mqtt_hostname
        self.mqtt_port = mqtt_port
        self.on_off_entity_name = FritzPowerPlug.ON_OFF_ENTITY_NAME.format(device_name = self.device_name)
        self.power_consumption_entity_name = FritzPowerPlug.POWER_CONSUMPTION_ENTITY_NAME.format(device_name = self.device_name)
        self.mqtt_trigger_off_topic = FritzPowerPlug.MQTT_TRIGGER_OFF_TOPIC.format(device_name = self.device_name)

        logging.debug((self.device_name, self.on_off_entity_name, self.power_consumption_entity_name, self.mqtt_trigger_off_topic))
        time_slice_start = datetime.date.today() - dateutil.relativedelta.relativedelta(days=7)
        time_slice_start_string = time_slice_start.strftime('%Y-%m-%d')

        qstr = f"select * from states where entity_id IN ('{self.on_off_entity_name}', '{self.power_consumption_entity_name}') and last_updated > '{time_slice_start_string}'::date order by state_id"
        logging.debug(qstr)

        ldf = pd.read_sql_query(qstr, con=engine)
        self.device_df = ldf.copy()

        self.time_slice_minutes_back = pd.to_datetime(datetime.datetime.now() - dateutil.relativedelta.relativedelta(minutes=time_slice_minutes_back)).tz_localize(tzlocal.get_localzone())

        ldf1 = ldf[ldf['entity_id'].isin([self.on_off_entity_name])].copy()
        ldf1['state'] = ldf1['state'].apply(convert_on_off_to_true_and_false).astype(float)
        self.on_off_entity_df = convert_to_time_slice_minutes_back_df(ldf1, self.time_slice_minutes_back)

        ldf1 = ldf[ldf['entity_id'].isin([self.power_consumption_entity_name])].copy()
        ldf1['state'] = ldf1['state'].apply(to_float).astype(float)
        self.power_consumption_entity_df = convert_to_time_slice_minutes_back_df(ldf1, self.time_slice_minutes_back)

    # switch off if for the last 12 minutes the power consumption was between off (< 0.5 Watt) and below work workload (~40 Watt)
    #  and the switch was not actively switched on in the last 12 minutes

    def should_switch_off(self):
        if self.was_switched_on_in_time_slice_minutes_back():
            return False

        if self.on_off() < 0.5: # currently switched off: nothing to do
            return False

        max_power_in_time_slice_minutes_back = self.max_power_in_time_slice_minutes_back()
        if max_power_in_time_slice_minutes_back < 0.5:
            return False

        if max_power_in_time_slice_minutes_back >= self.standby_limit_in_watt:
            return False

        return True

    def was_switched_on_in_time_slice_minutes_back(self):
        if len(self.on_off_entity_df) < 1:
            return False

        lds1 = self.on_off_entity_df['state']
        lds2 = lds1 - lds1.shift()
        lds2 = lds2[~pd.isnull(lds2)]
        lds3 = lds2[lds2 > 0]
        return len(lds3) > 0

    def on_off(self):
        if len(self.on_off_entity_df) < 1:
            if len(self.power_consumption_entity_df) < 1:
                return 0.0
            else:
                return 1.0

        return self.on_off_entity_df.iloc[-1,0]

    def power(self):
        if len(self.power_consumption_entity_df) < 1:
            return 0.0

        current_power = self.power_consumption_entity_df.iloc[-1,0]
        if self.on_off() < 0.5 and current_power > 0.5:
            raise Exception('Current power is greater than 0.5 Watt while the switch is assumed to be off!')

        return current_power

    def max_power_in_time_slice_minutes_back(self):
        max_power = np.nanmax(self.power_consumption_entity_df.iloc[:,0], initial=0.0)
        return max_power

    def check_switch_off(self):
        if not self.should_switch_off():
            logging.info("check_switch_off: do nothing")
            return

        logging.info(f"check_switch_off: publish: {self.mqtt_trigger_off_topic}: 'off'")
        paho.mqtt.publish.single(self.mqtt_trigger_off_topic, payload='off', qos=1, retain=False, hostname=self.mqtt_hostname, port=self.mqtt_port, keepalive=60, auth=self.mqtt_auth, protocol=paho.mqtt.client.MQTTv311, transport="tcp")

