"""Testing various endpoints on the Typhur IoT API"""

import asyncio
import json
import logging
import os

from aiohttp import ClientSession

from typhur_client import TyphurClient

async def main():
    """Everything discovered so far"""
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    async with ClientSession(
        json_serialize=lambda x: json.dumps(x, separators=(",", ":"))
    ) as session:
        client = TyphurClient(
            device_info="google sdk_gphone64_x86_64 15",
            device_sn="cc4d64f391f84fd8851714222dd200cd",
            websession=session,
        )
        response = await client.login(
            os.environ.get("TYPHUR_USERNAME"), os.environ.get("TYPHUR_PASSWORD")
        )
        print(str(response) + "\n" + "-" * 80, "\n")

        # shows a list of devices, strangely the app in my emulator didn't make this kind of request
        response = await client.request("app/device/bind/list")
        print(str(response) + "\n" + "-" * 80, "\n")

        # seems to show some cooking history
        response = await client.request("app/history/page", {"size": 20, "current": 1})
        print(str(response) + "\n" + "-" * 80, "\n")

        # Get the certificate to connect to the MQTT server, probably?
        response = await client.request("app/mqtt/cert/apply")
        print(str(response) + "\n" + "-" * 80, "\n")

        # mqtt_conn_param is interesting in this one
        response = await client.request("app/dict/list")
        print(str(response) + "\n" + "-" * 80, "\n")


if __name__ == "__main__":
    asyncio.run(main())

# Other URLs that are less interesting:
# - https://api.iot.typhur.com/app/article/list { "collectionId": <number> } - more ads / recipes?
# - https://api.iot.typhur.com/app/collection/list (seems to be ads / receipes)
# - https://api.iot.typhur.com/app/device/bind/list/refresh (not sure what this does, kicks off a background process - maybe MQTT?)
# - https://api.iot.typhur.com/app/device/model/list - all models offered
# - https://api.iot.typhur.com/app/favorite/page (favorite recipes?)
# - https://api.iot.typhur.com/app/notification/has/new
# - https://api.iot.typhur.com/app/ota/version/check - check for updates
# - https://api.iot.typhur.com/app/preset/page {"size": 20, "current": 1 } - this pattern is likely use elsewhere on "pages"
# - https://api.iot.typhur.com/app/user/get (user info)
# - https://api.iot.typhur.com/app/user/setting/get (user settings)
# Find other URLs by decompiling the Typhur app and searching for app/
