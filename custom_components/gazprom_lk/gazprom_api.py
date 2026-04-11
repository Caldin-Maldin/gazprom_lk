"""API для работы с личным кабинетом Газпром."""
import logging
import aiohttp
from typing import Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

class GazPromAPI:
    """API для взаимодействия с личным кабинетом."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        login: str,
        password: str
    ) -> None:
        """Initialize API."""
        self._session = session
        self._login = login
        self._password = password
        self._base_url = "https://xn--80afnfom.xn--80ahmohdapg.xn--80asehdb"

    async def async_authenticate(self) -> Dict[str, Any]:
        """Аутентификация в ЛК."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'Origin': self._base_url,
            'Referer': f'{self._base_url}/auth/sign-in',
            'X-Requested-With': 'XMLHttpRequest'
        }

        data_auth = {
            "operationName": "signInN3",
            "query": """mutation signInN3($deviceInfo: DeviceInfoInputV2!, $input: ClientSignInInputV2!) {
                signInN3(deviceInfo: $deviceInfo, input: $input) {
                    ok
                    error
                    hasAgreement
                    token
                    __typename
                }
            }""",
            "variables": {
                "deviceInfo": {
                    "appName": "desktop",
                    "appVersion": "7.8.8",
                    "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "device": "undefined",
                    "screenResolution": "1600x900",
                    "system": "Windows 10"
                },
                "input": {
                    "identifier": self._login,
                    "password": self._password,
                    "agreement": False,
                    "rememberMe": False
                }
            }
        }

        try:
            async with self._session.post(
                f'{self._base_url}/abr-lka-backend',
                json=data_auth,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    
                    if 'data' in response_json and 'signInN3' in response_json['data']:
                        signin_data = response_json['data']['signInN3']
                        
                        if signin_data.get('ok') is True and 'token' in signin_data:
                            return {
                                "auth_status": True,
                                "auth_message": "Авторизация успешна!",
                                "auth_token": signin_data['token']
                            }
                        else:
                            error_msg = signin_data.get('error', 'Неизвестная ошибка')
                            return {
                                "auth_status": False,
                                "auth_message": error_msg,
                                "auth_token": None
                            }
                    else:
                        return {
                            "auth_status": False,
                            "auth_message": "Некорректный ответ сервера",
                            "auth_token": None
                        }
                else:
                    return {
                        "auth_status": False,
                        "auth_message": f"Ошибка HTTP: {response.status}",
                        "auth_token": None
                    }
                    
        except aiohttp.ClientError as e:
            _LOGGER.error("Ошибка сети при аутентификации: %s", e)
            return {
                "auth_status": False,
                "auth_message": f"Ошибка сети: {str(e)}",
                "auth_token": None
            }
        except Exception as e:
            _LOGGER.error("Ошибка аутентификации: %s", e)
            return {
                "auth_status": False,
                "auth_message": str(e),
                "auth_token": None
            }

    async def async_get_info(self, token: str) -> Dict[str, Any]:
        """Получение информации из ЛК."""
        # Получение lsid
        lsid = await self._async_get_lsid(token)
        if not lsid:
            return {"error": "Не удалось получить ID лицевого счета"}

        # Получение данных ЛК
        data = await self._async_get_lk_data(token, lsid)
        return data

    async def _async_get_lsid(self, token: str) -> Optional[str]:
        """Получение ID личного кабинета."""
        headers = {
            'Token': token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'Origin': self._base_url,
            'Referer': f'{self._base_url}',
            'X-Requested-With': 'XMLHttpRequest'
        }

        data_lsid = {
            "operationName": "clientMessagesCount",
            "query": """query clientMessagesCount {
                clientMessagesCount {
                    ok
                    error
                    data {
                        notReadTotal
                        detailed {
                            lsId
                            isEls
                            notRead
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }""",
            "variables": {}
        }

        try:
            async with self._session.post(
                f'{self._base_url}/abr-lka-backend',
                json=data_lsid,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    
                    # Проверяем структуру ответа
                    if ('data' in response_json and 
                        'clientMessagesCount' in response_json['data'] and
                        'data' in response_json['data']['clientMessagesCount'] and
                        'detailed' in response_json['data']['clientMessagesCount']['data'] and
                        len(response_json['data']['clientMessagesCount']['data']['detailed']) > 0):
                        
                        lsid = response_json['data']['clientMessagesCount']['data']['detailed'][0].get('lsId')
                        if lsid is not None:
                            return str(lsid)
                        
        except aiohttp.ClientError as e:
            _LOGGER.error("Ошибка сети при получении lsid: %s", e)
        except Exception as e:
            _LOGGER.error("Ошибка получения lsid: %s", e)
        
        return None

    async def _async_get_lk_data(self, token: str, lsid: str) -> Dict[str, Any]:
        """Получение данных из ЛК."""
        headers = {
            'Token': token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'Origin': self._base_url,
            'Referer': f'{self._base_url}',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
        data_ls = {
            "operationName": "AccountInfo",
            "variables": {
                "account": {
                    "id": float(lsid) if lsid and lsid.replace('.', '', 1).isdigit() else 0,
                    "type": "LSPU"
                }
            },
            "query": """query AccountInfo($account: AccountInput!) {
                accountInfo(account: $account) {
                ok
                error
                data {
                  ...AccountInfo
                  parameters {
                    ...AccountParameter
                    __typename
                  }
                  providers {
                    ...AccountProvider
                    __typename
                  }
                  lspus {
                    ...AccountLspu
                    __typename
                  }
                  services {
                    ...AccountService
                    __typename
                  }
                  counters {
                    ...AccountCounter
                    __typename
                  }
                  equipments {
                    ...AccountEquipment
                    __typename
                  }
                  balances {
                    ...AccountBalance
                    __typename
                  }
                  acts {
                    ...AccountAct
                    __typename
                  }
                  contracts {
                    ...AccountContract
                    __typename
                  }
                  privileges {
                    ...AccountPrivilege
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
    
                fragment AccountInfoInsuranceConditionValue on InsuranceConditionValue {
                  text
                  boolean
                  __typename
                }
                
                fragment AccountInfoInsuranceConditionItem on InsuranceConditionItem {
                  name
                  value {
                    ...AccountInfoInsuranceConditionValue
                    __typename
                  }
                  __typename
                }
            
                fragment AccountInfoInsuranceHint on InsuranceConditionHints {
                  email {
                    ...AccountInfoInsuranceConditionItem
                    __typename
                  }
                  isFull {
                    ...AccountInfoInsuranceConditionItem
                    __typename
                  }
                  showInsurance {
                    ...AccountInfoInsuranceConditionItem
                    __typename
                  }
                  __typename
                }
                
                fragment AccountInfoInsurance on AccountInsuranceInfo {
                  id
                  serviceId
                  available
                  hints {
                    ...AccountInfoInsuranceHint
                    __typename
                  }
                  __typename
                }
                
                fragment AccountInfoPlaceholderAction on SectionAction {
                  text
                  type
                  __typename
                }
                
                fragment AccountInfoPlaceholder on SectionMessage {
                  type
                  text
                  action {
                    ...AccountInfoPlaceholderAction
                    __typename
                  }
                  __typename
                }
                
                fragment AccountInfoSettings on ComputedSettings {
                  aa
                  ais
                  ap
                  apsbp
                  amp
                  eis
                  epr
                  eags
                  eaps
                  ecas
                  eps
                  eprs
                  epi
                  snar
                  spro
                  aatch
                  aatco
                  aatp
                  upie
                  __typename
                }
                
                fragment AccountInfoNotification on AbonentInfoNotification {
                  id
                  title
                  content
                  lspuId
                  createDate
                  __typename
                }
                
                fragment AccountProviderType on ProviderType {
                  id
                  sort
                  code
                  name
                  measure: measureByDefault
                  __typename
                }
                
                fragment AccountProviderExchange on ProviderExchangeType {
                  id
                  code
                  name
                  description
                  __typename
                }
                
                fragment AccountProviderSettings on ProviderSettings {
                  aa
                  aatch
                  aatco
                  aatp
                  aatpi
                  aio
                  ais
                  aiz
                  amp
                  ap
                  apsbp
                  ccdm
                  epdl
                  epe
                  epi
                  epm
                  epr
                  isdm
                  mc
                  mis
                  paoe
                  pm
                  spro
                  tspo
                  __typename
                }
                
                fragment AccountLspuPlaceholder on LspuSections {
                  services
                  equipments
                  counters
                  contracts
                  balances
                  acts
                  parameters
                  privileges
                  __typename
                }
                
                fragment AccountServiceRegime on ConsumptionRegime {
                  abonentUuid
                  equipmentUuid
                  serviceUuid
                  regimeUuid
                  nodeUuid
                  counterCoefficient
                  norm
                  price
                  tariff
                  name
                  startDate
                  endDate
                  notification
                  __typename
                }
                
                fragment AccountServiceExecutor on ServiceExecutor {
                  id
                  name
                  __typename
                }
                
                fragment AccountServiceType on AdmServiceType {
                  id
                  name
                  code
                  __typename
                }
                
                fragment AccountServicePriceType on ProviderServicePriceType {
                  id
                  name
                  description
                  code
                  __typename
                }
                
                fragment AccountCounterValue on AbonentInfoCounterValue {
                  valueDay
                  valueMiddle
                  valueNight
                  overlap
                  rate
                  state
                  source
                  date
                  dateDt
                  __typename
                }
                
                fragment AccountCounterPrice on Price {
                  day
                  middle
                  night
                  __typename
                }
                
                fragment AccountBalanceChildren on AbonentInfoBalanceChild {
                  date
                  name
                  chargedSum
                  serviceUuid
                  __typename
                }
                
                fragment AccountActWork on AccountInfoActWork {
                  sum
                  serviceUuid
                  serviceName
                  equipmentUuid
                  equipmentName
                  __typename
                }
                
                fragment AccountInfo on AbonentInfoSummary {
                  id
                  number: account
                  type
                  isFull
                  alias
                  address
                  availableEls
                  paymentSourceAvailable
                  balance
                  epshCacheActualOn
                  insurance {
                    ...AccountInfoInsurance
                    __typename
                  }
                  placeholders: sectionMessages {
                    ...AccountInfoPlaceholder
                    __typename
                  }
                  settings: computed {
                    ...AccountInfoSettings
                    __typename
                  }
                  notifications {
                    ...AccountInfoNotification
                    __typename
                  }
                  __typename
                }
                
                fragment AccountParameter on AbonentInfoParameter {
                  lspuId
                  date
                  name
                  value
                  notification
                  __typename
                }
                
                fragment AccountProvider on AbonentInfoProvider {
                  id
                  name
                  type {
                    ...AccountProviderType
                    __typename
                  }
                  exchange: exchangeType {
                    ...AccountProviderExchange
                    __typename
                  }
                  settings {
                    ...AccountProviderSettings
                    __typename
                  }
                  __typename
                }
                
                fragment AccountLspu on AbonentInfoLspu {
                  id
                  providerId
                  number: account
                  alias
                  isFull
                  balance
                  commission: comissionTotal
                  placeholders: sections {
                    ...AccountLspuPlaceholder
                    __typename
                  }
                  __typename
                }
                
                fragment AccountService on AbonentInfoService {
                  lspuId
                  lspu
                  id
                  name
                  balance
                  balanceFrom
                  providerId
                  lastAmountForToday
                  sort
                  commissionType: comissionType
                  commissionRate: comissionRate
                  commissionAmount: comissionAmount
                  regimes: children {
                    ...AccountServiceRegime
                    __typename
                  }
                  executor {
                    ...AccountServiceExecutor
                    __typename
                  }
                  serviceType {
                    ...AccountServiceType
                    __typename
                  }
                  priceType {
                    ...AccountServicePriceType
                    __typename
                  }
                  __typename
                }
                
                fragment AccountCounter on AbonentInfoCounter {
                  lspuId
                  name
                  uuid
                  serialNumber
                  numberOfRates
                  capacity
                  stateInt
                  state
                  notification
                  averageRate
                  monthsCount
                  serviceName
                  serviceLinkId
                  needVerification
                  position
                  model
                  factorySeal
                  equipmentKind
                  meterType
                  checkDate
                  techSupportDate
                  sealDate
                  sealNumber
                  factorySealDate
                  commissionedOn
                  tariff
                  measure
                  values {
                    ...AccountCounterValue
                    __typename
                  }
                  price {
                    ...AccountCounterPrice
                    __typename
                  }
                  __typename
                }
                
                fragment AccountEquipment on AbonentInfoEquipment {
                  lspuId
                  type
                  name
                  uuid
                  serialNumber
                  state
                  stateInt
                  needVerification
                  numberOfRates
                  municipalResource
                  meterType
                  position
                  model
                  factorySeal
                  equipmentKind
                  date
                  checkDate
                  techSupportDate
                  sealNumber
                  sealDate
                  factorySealDate
                  commissionedOn
                  notification
                  __typename
                }
                
                fragment AccountBalance on AbonentInfoBalance {
                  lspuId
                  uuid
                  date
                  name
                  balanceStartSum
                  balanceEndSum
                  chargedSum
                  chargedVolume
                  circulationSum
                  forgivenDebt
                  organizationCode
                  paymentAdjustments
                  plannedSum
                  privilegeSum
                  privilegeVolume
                  restoredDebt
                  endBalanceApgp
                  prepaymentChargedAccumSum
                  debtSum
                  paidSum
                  temperatureCoefficient
                  notification
                  children {
                    ...AccountBalanceChildren
                    __typename
                  }
                  __typename
                }
                
                fragment AccountAct on AbonentInfoAct {
                  lspuId
                  uuid
                  name
                  date
                  notification
                  works {
                    ...AccountActWork
                    __typename
                  }
                  __typename
                }
                
                fragment AccountContract on AbonentInfoContract {
                  lspuId
                  active
                  name
                  number
                  serviceName
                  status
                  contractKind
                  description
                  uuid
                  serviceUuid
                  notification
                  beginDate
                  endDate
                  __typename
                }
                
                fragment AccountPrivilege on AbonentInfoPrivilege {
                  lspuId
                  abonentUuid
                  active
                  beginDate
                  endDate
                  name
                  notification
                  __typename
                }"""
        }
    
        try:
            async with self._session.post(
                f'{self._base_url}/abr-lka-backend',
                json=data_ls,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    
                    if 'data' in response_json and 'accountInfo' in response_json['data'] and 'data' in response_json['data']['accountInfo']:
                        info = response_json['data']['accountInfo']['data']
                        
                        # Базовые данные
                        ls_number = str(info.get('number', ''))
                        ls_balance_all = self._safe_float(info.get('balance', '0'))
                        
                        # Поиск баланса газа (как в вашем скрипте)
                        ls_balance_gas = 0.0
                        services_list = info.get('services', [])
                        gas_service = next((s for s in services_list if s.get('name') == 'Газоснабжение природным газом'), None)
                        if gas_service:
                            ls_balance_gas = self._safe_float(gas_service.get('balance', '0'))
                        
                        # Данные счетчика
                        ls_counter = ''
                        counterid = ''
                        ls_value_gas = 0.0
                        ls_rate_gas = 0.0
                        ls_value_date = ''
                        ls_last_value_gas = 0.0
                        ls_last_value_date = ''
                        
                        counters = info.get('counters', [])
                        if counters and len(counters) > 0:
                            counter = counters[0]
                            ls_counter = str(counter.get('name', ''))
                            counterid = str(counter.get('uuid', ''))
                            
                            values = counter.get('values', [])
                            if values and len(values) > 0:
                                value_data = values[0]
                                ls_value_gas = self._safe_float(value_data.get('valueDay', '0'))
                                ls_rate_gas = self._safe_float(value_data.get('rate', '0'))
                                ls_value_date = str(value_data.get('date', ''))

                                if len(values) > 1:
                                    last_value_data = values[1]
                                    ls_last_value_gas = self._safe_float(last_value_data.get('valueDay', '0'))
                                    ls_last_value_date = str(last_value_data.get('date', ''))
                                else:
                                    ls_last_value_gas = 0.0
                                    ls_last_value_date = ''


                        result = {
                            'ls_number': ls_number,
                            'ls_balance_all': ls_balance_all,
                            'ls_balance_gas': ls_balance_gas,
                            'ls_counter': ls_counter,
                            'ls_value_gas': ls_value_gas,
                            'ls_rate_gas': ls_rate_gas,
                            'ls_value_date': ls_value_date,
                            'lsid': lsid,
                            'counterid': counterid,
                            'ls_last_value_gas': ls_last_value_gas,
                            'ls_last_value_date': ls_last_value_date,                            
                            'error': ''
                        }
                        
                        return result
                    else:
                        error_msg = response_json.get('errors', [{}])[0].get('message', 'Некорректная структура ответа') if 'errors' in response_json else 'Некорректная структура ответа'
                        return {'error': error_msg}
                else:
                    return {'error': f"Ошибка HTTP: {response.status}"}
                    
        except aiohttp.ClientError as e:
            _LOGGER.error("Ошибка сети при получении данных ЛК: %s", e)
            return {'error': f"Ошибка сети: {str(e)}"}
        except Exception as e:
            _LOGGER.error("Ошибка получения данных ЛК: %s", e)
            return {'error': str(e)}

    async def async_send_indication(self, token: str, lsid: str, counterid: str, value: float) -> Dict[str, Any]:
        """Передача показаний."""
        headers = {
            'Token': token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'Origin': self._base_url,
            'Referer': f'{self._base_url}',
            'X-Requested-With': 'XMLHttpRequest'
        }

        data_send = {
            "operationName": "indicationSendV4",
            "query": """mutation indicationSendV4($deviceInfo: DeviceInfoInputV2!, $input: IndicationSendV4Input!) {
                indicationSendV4(deviceInfo: $deviceInfo, input: $input) {
                    ok
                    error
                    data {
                        lspuId
                        online
                        calculated
                        counters {
                            uuid
                            sent
                            message
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }""",
            "variables": {
                "input": {
                    "lspuGroups": [{
                        "lspuId": float(lsid) if lsid and lsid.replace('.', '', 1).isdigit() else 0,
                        "counters": [{
                            "uuid": counterid,
                            "serviceId": 1424,
                            "valueDay": float(value),
                            "valueNight": 0.0,
                            "valueMiddle": 0.0,
                            "overlapDay": False,
                            "overlapMiddle": False,
                            "overlapNight": False
                        }]
                    }]
                },
                "deviceInfo": {
                    "appName": "desktop",
                    "appVersion": "7.8.8",
                    "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "device": "undefined",
                    "screenResolution": "1280x1024",
                    "system": "Windows 10"
                }
            }
        }

        try:
            async with self._session.post(
                f'{self._base_url}/abr-lka-backend',
                json=data_send,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    
                    if ('data' in response_json and 
                        'indicationSendV4' in response_json['data'] and
                        'data' in response_json['data']['indicationSendV4'] and
                        len(response_json['data']['indicationSendV4']['data']) > 0 and
                        'counters' in response_json['data']['indicationSendV4']['data'][0] and
                        len(response_json['data']['indicationSendV4']['data'][0]['counters']) > 0):
                        
                        result_data = response_json['data']['indicationSendV4']['data'][0]['counters'][0]
                        message = result_data.get('message', 'Показания переданы')
                        success = result_data.get('sent', False)
                        
                        return {
                            "result": message,
                            "success": success,
                            "message": message
                        }
                    else:
                        return {
                            "result": "Ошибка в структуре ответа",
                            "success": False,
                            "message": "Ошибка в структуре ответа"
                        }
                else:
                    return {
                        "result": f"Ошибка HTTP: {response.status}",
                        "success": False,
                        "message": f"Ошибка HTTP: {response.status}"
                    }
                    
        except aiohttp.ClientError as e:
            _LOGGER.error("Ошибка сети при передаче показаний: %s", e)
            return {
                "result": f"Ошибка сети: {str(e)}",
                "success": False,
                "message": f"Ошибка сети: {str(e)}"
            }
        except Exception as e:
            _LOGGER.error("Ошибка передачи показаний: %s", e)
            return {
                "result": str(e),
                "success": False,
                "message": str(e)
            }

    def _safe_float(self, value: Any) -> float:
        """Безопасное преобразование в float."""
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Убираем пробелы и запятые
                cleaned = value.replace(' ', '').replace(',', '.')
                return float(cleaned)
            return 0.0
        except (ValueError, TypeError):
            return 0.0