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
    # activation_id=3807035855 phone_number='79238944456' activation_cost=0.2 
    # country_code='0' can_get_another_sms=True activation_time='2025-07-08 10:49:27' 
    # operator='mtt' 
    
    code = await number.wait_sms_code(timeout=300)
    print(code) # 1234
    
    status = await number.get_activation_status()
    
    await number.set_activation_status(SetActivationStatus.CANCEL) # Отменить номер || Cancel number
    await number.set_activation_status(8) # Отменить номер || Cancel number
    
asyncio.run(main())
```
