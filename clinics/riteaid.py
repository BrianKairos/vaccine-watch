import os
from datetime import datetime

from geopy.distance import distance
from pytz import timezone

from .vaccine_spotter import VaccineSpotterClinic


class RiteAid(VaccineSpotterClinic):
    def __init__(self):
        self.here = (os.environ["LATITUDE"], os.environ["LONGITUDE"])
        super().__init__()

    def should_include_location(self, location):
        coordinates = location["geometry"]["coordinates"]
        longitude, latitude = coordinates
        return location["properties"]["provider_brand"] == "rite_aid" and distance(
            self.here, (latitude, longitude)
        ).miles < int(os.environ["RADIUS"])

        #     print("{} #{}: {}".format(location["properties"]["provider_brand"],
        #                               location["properties"]["provider_location_id"],
        #                               location["properties"]["city"]))
        #     return True
        # else:
        #     dist = distance(self.here, (latitude, longitude)).miles
        #     print("{} out of range: {}".format(location["properties"]["city"], dist))

    def format_data(self, location):
        zone = os.environ.get("TIMEZONE", "US/Pacific")
        try:
            if location["properties"]["appointments_last_fetched"]:
                appointments_last_fetched = (
                    datetime.fromisoformat(
                        location["properties"]["appointments_last_fetched"]
                    )
                        .astimezone(timezone(zone))
                        .strftime("%-I:%M")
                )
            else:
                appointments_last_fetched = None
        except (
                ValueError,
                TypeError,
        ) as e:  # Python doesn't like 2 digits for decimal fraction of second
            appointments_last_fetched = None

        return {
            "link": location["properties"]["url"],
            "id": "{}riteaid-{}".format(
                os.environ.get("CACHE_PREFIX", ""), location["properties"]["id"]
            ),
            "name": "RiteAid {}".format(
                " ".join(
                    [
                        word.capitalize()
                        for word in location["properties"]["city"].split(" ")
                    ]
                )
            ),
            "state": location["properties"]["state"],
            "zip": location["properties"]["postal_code"],
            "appointments_last_fetched": appointments_last_fetched,
        }
