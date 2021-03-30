import json
import logging
import os

import requests

from utils import timeout_amount

from . import Clinic


class RiteAid(Clinic):
    def __init__(self):
        # self.allow_list = json.loads(os.environ["CVS_ALLOW_LIST"])
        # self.block_list = json.loads(os.environ.get("CVS_BLOCK_LIST", "{}"))
        self.states = json.loads(os.environ["STATES"])
        self.latitude = json.loads(os.environ["LATITUDE"])
        self.longitude = json.loads(os.environ["LONGITUDE"])
        self.radius = json.loads(os.environ["RADIUS"])

    def get_locations(self):

        locations_with_vaccine = []
        locations_without_vaccine = []
        headers = {'User-Agent': 'Mozilla/5.0'}

        fetch_stores_riteaid_url = 'https://www.riteaid.com/services/ext/v2/stores/getStores?latitude={}&longitude={}&radius={}'.format(
            self.latitude, self.longitude, self.radius
        )
        nearby_stores = requests.get(fetch_stores_riteaid_url, timeout=timeout_amount)

        try:
            nearby_stores.raise_for_status()
            for store in nearby_stores.json()['Data']['stores']:
                url = "https://www.riteaid.com/services/ext/v2/vaccine/checkSlots?storeNumber={}".format(
                    store['storeNumber'])
                logging.info("{} {}: #{}".format(store['city'], store['address'], store['storeNumber']))
                avail = (requests.get(url=url, headers=headers)).json()
                if avail['Status'] == "SUCCESS":
                    logging.info("  {} first doses, {} second doses".format(avail['Data']["slots"]['1'],
                                                                            avail['Data']['slots']['2']))
                    if avail['Data']['slots']['1']:
                        locations_with_vaccine.append(format_data(store))
                    else:
                        locations_without_vaccine.append(format_data(store))
                else:
                    logging.warning("  Query failed for store {}.".format(store['storeNumber']))

                # for location in locations:
                #     if location["city"] in self.allow_list[state]:
                #         if location["status"] == "Available":
                #             if site_locked_out:
                #                 logging.info(
                #                     "Would have notified for CVS %s, %s but site is locked out",
                #                     location["city"],
                #                     state,
                #                 )
                #             else:
                #                 locations_with_vaccine.append(format_data(location))
                #         elif location["status"] == "Fully Booked":
                #             locations_without_vaccine.append(format_data(location))
                #         else:
                #             logging.error(
                #                 "Unknown location status from CVS: %s",
                #                 location["status"],
                #             )
                #     elif (
                #         state not in self.block_list
                #         or location["city"] not in self.block_list[state]
                #     ):
                #         logging.warning(
                #             "New city found for CVS: %s, %s. Add to allow list or block list.",
                #             location["city"],
                #             state,
                #         )

        except requests.exceptions.RequestException:
            logging.exception(
                "Bad response from RiteAid",
            )

        return {
            "with_vaccine": locations_with_vaccine,
            "without_vaccine": locations_without_vaccine,
        }


def format_data(location):
    return {
        "id": "{}riteaid-{}".format(
            os.environ.get("CACHE_PREFIX", ""), location["storeNumber"]
        ),
        "state": location["state"],
        "name": "RiteAid {}".format(
            " ".join([word.capitalize() for word in location["city"].split(" ")])
        ),
        "locationDescription": location['locationDescription'],
        "link": "https://www.riteaid.com/services/ext/v2/vaccine/checkSlots?storeNumber={}".format(location['storeNumber']),
    }
