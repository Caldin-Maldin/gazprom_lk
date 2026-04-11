"""Константы для Gazprom LK."""
from datetime import timedelta
import logging

DOMAIN = "gazprom_lk"
LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
UPDATE_INTERVAL = None

CONF_LOGIN = "login"
CONF_PASSWORD = "password"
CONF_LS_NUMBER = "ls_number"

ATTR_BALANCE_ALL = "balance_all"
ATTR_BALANCE_GAS = "balance_gas"
ATTR_COUNTER_NAME = "counter_name"
ATTR_COUNTER_VALUE = "counter_value"
ATTR_COUNTER_LAST_VALUE = "counter_last_value"
ATTR_COUNTER_RATE = "counter_rate"
ATTR_VALUE_DATE = "value_date"
ATTR_LAST_VALUE_DATE = "last_value_date"
ATTR_LSID = "lsid"
ATTR_COUNTERID = "counterid"
ATTR_COUNTER_FULL_NAME = "counter_full_name"  
ATTR_LAST_INDICATION_DATE = "last_indication_date"  

SERVICE_SEND_INDICATION = "send_indication"
SERVICE_UPDATE_DATA = "update_data"