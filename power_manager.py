import asyncio
from datetime import datetime, timedelta
from tesla_api import TeslaApiClient

email = 'yourEmail@domain.com'
password = 'yourTeslaAccountPassword'

# set summer start/end months
summer_first_month = 5
summer_last_month = 10

# set peak start/end times (in 24-hour format; eg. 17 = 5pm)
summer_peak_start_hour = 14
summer_peak_end_hour = 20
winter_morning_peak_start_hour = 5
winter_morning_peak_end_hour = 9
winter_evening_peak_start_hour = 17
winter_evening_peak_end_hour = 21

# fetch current datetime
current = datetime.now()
print("\ncurrent date & time is {}".format(current))


async def main():
    client = TeslaApiClient(email, password)
    energy_sites = await client.list_energy_sites()
    print("Number of energy sites = %d" % (len(energy_sites)))
    assert(len(energy_sites)==1)
    cur_mode = await energy_sites[0].get_operating_mode()
    print("current operating mode = {}\n".format(cur_mode))
    if await season_check() == "winter":
        # change peak period integers into time objects; begin peak 10 minutes early
        morning_start = (datetime(2021,1,1,winter_morning_peak_start_hour) - timedelta(minutes=10)).time()
        evening_start = (datetime(2021,1,1,winter_evening_peak_start_hour) - timedelta(minutes=10)).time()
        morning_end = datetime(2021,1,1,winter_morning_peak_end_hour).time()
        evening_end = datetime(2021,1,1,winter_evening_peak_end_hour).time()
        # check if weekday and within peak hours
        if current.weekday() < 5 and (
            morning_start < current.time() < morning_end or
            evening_start < current.time() < evening_end):
            print("PEAK hours in effect!")
            # TODO: skip changing mode if mode is already self_consumption
            await set_onpeak(energy_sites)
        else:
            print("it is currently OFF-PEAK")
            # TODO: skip changing mode if mode is already backup
            await set_offpeak(energy_sites)
    else: # it is summer
        # change peak period integers into time objects; begin peak 10 minutes early
        peak_start = (datetime(2021,1,1,summer_peak_start_hour) - timedelta(minutes=10)).time()
        peak_end = datetime(2021,1,1,summer_peak_end_hour).time()
        # check if weekday and within peak hours
        if current.weekday() < 5 and (peak_start < current.time() < peak_end):
            print("PEAK hours in effect!")
            # TODO: skip changing mode if mode is already self_consumption
            await set_onpeak(energy_sites)
        else:
            print("it is currently OFF-PEAK")
            # TODO: skip changing mode if mode is already backup
            await set_offpeak(energy_sites)
    print("\n\n")
    await client.close()


async def set_offpeak(energy_sites):
    print("attempting to change mode to backup-only (backup)...")
    await energy_sites[0].set_operating_mode_backup()
    new_mode = await energy_sites[0].get_operating_mode()
    print("operating mode set to: {}".format(new_mode))

async def set_onpeak(energy_sites):
    print("attempting to change mode to self powered (self-consumption)...")
    await energy_sites[0].set_operating_mode_self_consumption()
    new_mode = await energy_sites[0].get_operating_mode()
    print("operating mode set to: {}".format(new_mode))

# season check
async def season_check():
    if (summer_first_month <= current.month <= summer_last_month):
        print("summer-season is in effect")
        return("summer")
    else:
        print("winter-season is in effect")
        return("winter")

asyncio.run(main())
