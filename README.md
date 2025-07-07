# AioSmsActivate 

<div align="center">

[![AioSmsProviders - aiosmsactivate](https://img.shields.io/static/v1?label=lolkof&message=AIOSMSACTIVATE&color=blue&logo=github)](https://github.com/AioSmsProviders/aiosmsactivate "Go to GitHub repo")

[SMS-ACTIVATE Official documentation](https://sms-activate.page/api2)

[ДОКУМЕНТАЦИЯ](https://aiosmsproviders.github.io/aiosmsactivate/aiosmsactivate/client.html)
[DOCUMENTATION](https://aiosmsproviders.github.io/aiosmsactivate/aiosmsactivate/client.html)

</div>

## Getting Started

### first steps (beta)

```python
from aiosmsactivate import SmsActivate

import asyncio

sa = SmsActivate('token')

async def main():
    balance = await sa.get_balance()
    print(balance)
    # 6.25
    
    number = await sa.purchase('ya')
    print(number)
    # {'activationId': '3805286977', 'phoneNumber': '79148410549', 
    # 'activationCost': 0.2, 'currency': 840, 'countryCode': '0', 
    # 'canGetAnotherSms': True, 'activationTime': '2025-07-07 23:58:13', 
    # 'activationEndTime': '2025-07-08 00:38:13', 'activationOperator': 'mts'}
    
    number = await sa.purchase_v1('ya')
    print(number)
    # ACCESS_NUMBER:3805353105:79146307636
    
asyncio.run(main())
```
