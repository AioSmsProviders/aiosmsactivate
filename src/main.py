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
    
async def test():
    # number = await sa.purchase('ya')
    # number.activation_id # 3807035855
    # number.phone_number # '79238944456'
    # number.operator # 'mtt'
    # print(number)
    # await sa.set_activation_status(3807227097, SetActivationStatus.AGAIN) #79146308060
    # number = await sa.purchase('bd')
    number = 3807407396 # 79140519731
    print(number)
    resp = await sa.wait_sms_code(number) 
    print(resp)
    input('Ждём отправки смс')
    resp = await sa.wait_sms_code(number)
    print(resp)
    
asyncio.run(test())