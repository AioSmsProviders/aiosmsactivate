# AioSmsActivate 

<div align="center">

[![AioSmsProviders - aiosmsactivate](https://img.shields.io/static/v1?label=AioSmsProviders&message=AIOSMSACTIVATE&color=blue&logo=github)](https://github.com/AioSmsProviders/aiosmsactivate "Go to GitHub repo")

[SMS-ACTIVATE Official documentation](https://sms-activate.page/api2?ref=1707310)

[ДОКУМЕНТАЦИЯ](https://aiosmsproviders.github.io/aiosmsactivate/aiosmsactivate/client.html)
[DOCUMENTATION](https://aiosmsproviders.github.io/aiosmsactivate/aiosmsactivate/client.html)

</div>

## Getting Started

### Simple usage

```python
from aiosmsactivate import SmsActivate
from aiosmsactivate.types import SetActivationStatus

import asyncio


sa = SmsActivate('token')

async def main():
    balance = await sa.get_balance()
    print(balance) # 6.25
    
    number = await sa.purchase('ya')
    number.activation_id # 3807035855
    number.phone_number # '79238944456'
    number.operator # 'mtt'
    print(number)
    # activation_id=3809954454 phone_number='79927146212' activation_cost=0.2 
    # country_code='0' can_get_another_sms=True activation_time='2025-07-09 01:14:45' 
    # operator='mtt' activation_unix_time=1654093857
    
    code = await number.wait_sms_code(timeout=300)
    print(code) # 1234
    
    status = await number.get_activation_status()
    
    await number.set_activation_status(SetActivationStatus.CANCEL) # Отменить номер || Cancel number
    await number.set_activation_status(8) # Отменить номер || Cancel number

    service = await sa.get_service('ya', 0) # 0 it is ru country
    print(service)
    # code='ya' name='Yandex/Uber' country='0' 
    # price=0.115 retail_price=0.2 free_price_map={'0.3067': 17134, '0.3065': 16996, ...} 
    # count=11049 physical_count=5334
    
asyncio.run(main())
```
