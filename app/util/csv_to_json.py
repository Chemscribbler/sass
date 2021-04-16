import csv
import json
from datetime import date


def export_json(input_csv, name):
    """
        Creates json that matches ABR format
        """
    e_json = {
        "name": name,
        "date": date.today().strftime("%Y-%m-%d"),
        "cutToTop": 0,
        "preliminaryRounds": 0,
        "tournamentOrganiser": {"nrdbId": "", "nrdbUsername": "YsengrinSC"},
        "players": [],
        "eliminationPlayers": {},
        "uploadedFrom": "SASS",
        "links": {
            0: {
                "rel": "schemaderivedfrom",
                "href": "http://steffens.org/nrtm/nrtm-schema.json",
            },
            1: {
                "rel": "uploadedfrom",
                "href": "https://github.com/Chemscribbler/Netrunner/tree/main/SingleSided_App",
            },
        },
    }

    with open(input_csv, "r", encoding="cp1257") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            e_json["players"].append(
                {
                    "id": count,
                    "name": row["Player"],
                    "rank": row["Position"],
                    "corpIdentity": row["Corp"],
                    "runnerIdentity": row["Runner"],
                    "matchPoints": row["Score"],
                    "strengthOfSchedule": round(float(row["SoS"]), 4),
                    "extendedStrengthOfSchedule": round(float(row["eSoS"]), 6),
                    "sideBalance": row["SideBalance"],
                }
            )
            count += 1

    return e_json


if __name__ == "__main__":
    file_name = input("File Name: ")
    t_name = input("Tournament Name: ")
    with open("results.json", "w") as outfile:
        json.dump(export_json(file_name, t_name), outfile)

