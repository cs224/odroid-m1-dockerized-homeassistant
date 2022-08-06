import logging
import click

import ha


def main_(mqtt_user, mqtt_passwd):
    logging.debug((mqtt_user, mqtt_passwd))

    if mqtt_user is None:
        mqtt_user = 'mqttuser'

    if mqtt_passwd is None:
        mqtt_passwd = 'mqttpasswd'

    ladestation = ha.ladestation = ha.FritzPowerPlug('ladestation', standby_limit_in_watt=10.0, mqtt_auth = dict(username=mqtt_user, password=mqtt_passwd), mqtt_hostname="localhost", mqtt_port=1883)
    ladestation.check_switch_off()

@click.command()
@click.option('--mqtt-user', '-u', help='The MQTT user')
@click.option('--mqtt-passwd', '-p', help='The MQTT password')
def main(mqtt_user, mqtt_passwd):
    """Check for standby mode power currents and turn them off."""

    try:
        main_(mqtt_user, mqtt_passwd)
    except Exception as ex:
        logging.exception(ex)
    print('Trigger power off for standby finished running.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.warning("Starting")
    main()
