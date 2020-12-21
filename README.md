# power_manager.py - AWS Lambda deployment
1) download aws_tesla_power_manager.zip and deploy as package to AWS Lambda
2) set lambda function environment variables "email" and "pwrd" to your tesla.com username and password
3) edit the file if needed to adjust peak times (set for Arizona SRP E-15 & E-27 price plans as of 12/2020)
4) create 2 eventbridge schedules - one just prior to peak periods, and one immediately following peak. Eventbridge & Cloudwatch are in UTC. As a simplification, this script runs more than necessary, so as to accomodate everything in 2 cron jobs. Additionally, this avoids confusion and having to account for date difference on 4/30, where the 9pm "offpeak" would be 5/1 UTC, and then run at an incorrect time due to the season change.
Below are the cron schedules for on/off based on SRP e-15 and e-27 priceplans:
Cron for off-peak (03:02, 04:02, and 16:02 UTC, which is 8:02pm, 9:02pm, and 9:02 am, respectively)
```
cron(2 3,4,16 ? * * *)
```
Cron for on-peak (11:58, 20:58, and 23:58 UTC, which is 4:58am, 1:58pm, and 4:58pm, respectively)
```
cron(58 11,20,23 ? * * *)
```


# power_manager.py - Local install

Requires: python 3.7+, aiohttp

update variables within power_manager.py to reflect your own email & password, and adjust summer season months and peak hours as desired. The script automatically subtracts 10 minutes from the start of each peak window, so this can be called via cronjobs a few minutes prior to the actual peak start time, and immediately following conclusion of the peak window.

The seasons and peak windows are already set for SRP's pricing plans for E-15 and E-27 price plans as of 12/15/2020 (below).
```
Summer - 5/1-10/31 2pm-8pm
Winter - 11/1-4/30 5am-9am and 5pm-9pm
```
The crontab I setup for this script is below. I intentionally let it run weekends as well, and handle weekend/weekdays within the python script. The script does not currently account for holidays.
```
#run for peak-starts at xx:57
57 4,13,16 * * * python3 /root/tesla_api/power_manager.py >> /var/log/power_manager.log
#run for peak-ends at xx:03
3  9,20,21 * * * python3 /root/tesla_api/power_manager.py >> /var/log/power_manager.log
```


# Below is from forked repo.


# Tesla API

This is a package for connecting to the Tesla API.

## Usage for a vehicle

```python
import asyncio
from tesla_api import TeslaApiClient

async def main():
    async with TeslaApiClient('your@email.com', 'yourPassword') as client:
        vehicles = await client.list_vehicles()

        for v in vehicles:
            print(v.vin)
            await v.controls.flash_lights()

asyncio.run(main())
```


## Usage for Powerwall 2

```python
import asyncio
from tesla_api import TeslaApiClient

async def main():
    client = TeslaApiClient('your@email.com', 'yourPassword')

    energy_sites = await client.list_energy_sites()
    print("Number of energy sites = %d" % (len(energy_sites)))
    assert(len(energy_sites)==1)
    reserve = await energy_sites[0].get_backup_reserve_percent()
    print("Backup reserve percent = %d" % (reserve))
    print("Increment backup reserve percent")
    await energy_sites[0].set_backup_reserve_percent(reserve+1)

    await client.close()

asyncio.run(main())
```


## Reusing API tokens

To avoid needing to store login details, you can pass in a previous API token.
Each time a new API token is created (either from a new login, or by refreshing an
expired token), the `on_new_token` callback will be called.

```python
async def save_token(token):
    open("token_file", "w").write(token)

async def main():
    email = password = token = None
    try:
        token = open("token_file").read()
    except OSError:
        email = input("Email> ")
        password = input("Password> ")
    client = TeslaApiClient(email, password, token, on_new_token=save_token)
    ...
```

If you only want to verify and save a user's token for later use,
you could use the `authenticate()` method:
```python
async def main():
    async with TeslaApiClient(email, password, on_new_token=save_token) as client:
        await client.authenticate()
```
