"""Константы для Gazprom LK."""
from datetime import timedelta
import logging

DOMAIN = "gazprom_lk"  # Изменили с "gazprom_lk" на "gas"
LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
# Убрали автообновление - оставляем только None
UPDATE_INTERVAL = None  # Изменили с timedelta(minutes=30)

CONF_LOGIN = "login"
CONF_PASSWORD = "password"
CONF_LS_NUMBER = "ls_number"

ATTR_BALANCE_ALL = "balance_all"
ATTR_BALANCE_GAS = "balance_gas"
ATTR_COUNTER_NAME = "counter_name"
ATTR_COUNTER_VALUE = "counter_value"
ATTR_COUNTER_RATE = "counter_rate"
ATTR_VALUE_DATE = "value_date"
ATTR_LSID = "lsid"
ATTR_COUNTERID = "counterid"

SERVICE_SEND_INDICATION = "send_indication"
SERVICE_UPDATE_DATA = "update_data"