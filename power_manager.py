from datetime import datetime as dt, timedelta
from os import environ
import dateutil.tz
import asyncio
from tesla_api.tesla_api import TeslaApiClient

#pricing season start/end
summer_first_month = 5
summer_last_month = 10
# Peak pricing start/end hours
timezone = 'US/Arizona' 
summer_start = 14
summer_end = 20
winter_morning_start = 5
winter_morning_end = 9
winter_evening_start = 17
winter_evening_end = 21

az = dateutil.tz.gettz(timezone)
current = dt.now(tz=az)
email = environ['email']
pwrd = environ['pwrd']


def lambda_handler(event, context):
    asyncio.run(main())
    return


async def main():
    client = TeslaApiClient(email, pwrd)
    energy_sites = await client.list_energy_sites()
    assert(len(energy_sites)==1)
    cur_mode = await energy_sites[0].get_operating_mode()
    print(f"Current Mode: {cur_mode}")
    season = "summer" if (
        summer_first_month <= current.month <= summer_last_month
        ) else "winter"
    if await is_peak(season):
        print(f"Pricing: {season.upper()} ON-PEAK")
        if cur_mode == "self_consumption":
            print("Mode already set to self-consumption.")
        else:
            print("Changing to self-consumption.")
            await energy_sites[0].set_operating_mode_self_consumption()
            new_mode = await energy_sites[0].get_operating_mode()
            print(f"New Mode: {new_mode}")
    else:
        print(f"Pricing: {season.upper()} OFF-PEAK")        
        if cur_mode == "backup":
            print("Mode already set to backup.")
        else:
            print("Changing to backup.")
            await energy_sites[0].set_operating_mode_backup()
            new_mode = await energy_sites[0].get_operating_mode()
            print(f"New Mode: {new_mode}")            
    await client.close()


async def is_peak(season):
    if season == "winter": # is it winter
        morn_start = (dt.strptime(str(winter_morning_start),"%H")
                      - timedelta(minutes=10)
                      ).time()
        morn_end = dt.strptime(str(winter_morning_end),"%H").time()
        eve_start = (dt.strptime(str(winter_evening_start), "%H")
                     - timedelta(minutes=10)
                     ).time()
        eve_end = dt.strptime(str(winter_evening_end), "%H").time()
        # True if weekday between peak times
        return current.weekday() < 5 and \
               (morn_start < current.time() < morn_end or 
                eve_start < current.time() < eve_end)
    else: # it is summer
        start = (dt.strptime(str(summer_peak_start_hour),"%H") 
                 - timedelta(minutes=10)).time()
        end = dt.strptime(str(summer_peak_end_hour),"%H").time()
        # True if weekday between peak times
        return current.weekday() < 5 and (start < current.time() < end)
