#!/usr/bin/env python

# Copyright 2012-2019 Gerwin Sturm
#
# Thanks to all contributors:
# https://github.com/Scarygami/location-history-json-converter/graphs/contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division

import sys
import json
import math
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime

try:
    import ijson
except ImportError:
    ijson_available = False
else:
    ijson_available = True


def _valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise ArgumentTypeError(msg)


def _check_date(timestampms, startdate, enddate):
    dt = datetime.utcfromtimestamp(int(timestampms) / 1000)
    if startdate and startdate > dt:
        return False
    if enddate and enddate < dt:
        return False
    return True


def _read_activity(arr):
    ret = {}
    if len(arr) == 1 and "activity" in arr[0]:
        items = arr[0]["activity"]
        for item in items:
            if "type" in item and "confidence" in item:
                ret[item["type"]] = item["confidence"]
    return ret


def _distance(lat1, lon1, lat2, lon2):
    """ Returns the distance between to two coordinates in KM using the Haversine formula"""
    R = 6371  # Radius of the earth in km
    dlat = _deg2rad(lat2-lat1)
    dlon = _deg2rad(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(_deg2rad(lat1)) * math.cos(_deg2rad(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c  # Distance in km
    return d


def _deg2rad(deg):
    return deg * (math.pi/180)


def convert(locations, output, format="kml", js_variable="locationJsonData",
            start_date=None, end_date=None, chronological=False, separator=","):
    """Converts the provided locations to the specified format

    Parameters
    ----------

    locations : Iterable
        list or other Iterable of locations from Google Takeout JSON file

    output: File or StringIO or similar
        All output will be written to this buffer

    format: str
        Format to convert to, can be "kml", "json", "csv", "csvfull", "csvfullest", "js", "gpx", "gpxtracks"

    js_variable: str
        Variable name to be used for js output

    start_date: datetime
        Locations before this date will be ignored

    end_date: datetime
        Locations after this date will be ignored

    chronological: bool
        Whether to sort all timestamps in chronological order (required for gpxtracks)

    separator: str
        What separator to use for the csv formats
    """

    if start_date or end_date:
        locations = [item for item in locations if _check_date(item["timestampMs"], start_date, end_date)]

    if chronological or format == "gpxtracks":
        locations = sorted(locations, key=lambda item: item["timestampMs"])

    if format == "json" or format == "js":
        if format == "js":
            output.write("window.%s = " % js_variable)

        output.write("{\"locations\":[")
        first = True

        for item in locations:
            if 'longitudeE7' in item and 'latitudeE7' in item:
                if item["latitudeE7"] > 1800000000:
                    item["latitudeE7"] = item["latitudeE7"] - 4294967296
                if item["longitudeE7"] > 1800000000:
                    item["longitudeE7"] = item["longitudeE7"] - 4294967296
                if first:
                    first = False
                else:
                    output.write(",")
                output.write("{")
                output.write("\"timestampMs\":%s," % item["timestampMs"])
                output.write("\"latitudeE7\":%s," % item["latitudeE7"])
                output.write("\"longitudeE7\":%s" % item["longitudeE7"])
                output.write("}")

        output.write("]}")
        if format == "js":
            output.write(";")

    if format == "csv":
        output.write(separator.join(["Time", "Latitude", "Longitude"]) + "\n")
        for item in locations:
            if 'longitudeE7' in item and 'latitudeE7' in item:
                if item["latitudeE7"] > 1800000000:
                    item["latitudeE7"] = item["latitudeE7"] - 4294967296
                if item["longitudeE7"] > 1800000000:
                    item["longitudeE7"] = item["longitudeE7"] - 4294967296
                output.write(separator.join([
                    datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "%.8f" % (item["latitudeE7"] / 10000000),
                    "%.8f" % (item["longitudeE7"] / 10000000)
                ]) + "\n")

    if format == "csvfull":
        output.write(separator.join([
            "Time", "Latitude", "Longitude", "Accuracy", "Altitude", "VerticalAccuracy", "Velocity", "Heading"
        ]) + "\n")
        for item in locations:
            if 'longitudeE7' in item and 'latitudeE7' in item:
                if item["latitudeE7"] > 1800000000:
                    item["latitudeE7"] = item["latitudeE7"] - 4294967296
                if item["longitudeE7"] > 1800000000:
                    item["longitudeE7"] = item["longitudeE7"] - 4294967296
                output.write(separator.join([
                    datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "%.8f" % (item["latitudeE7"] / 10000000),
                    "%.8f" % (item["longitudeE7"] / 10000000),
                    str(item.get("accuracy", "")),
                    str(item.get("altitude", "")),
                    str(item.get("verticalAccuracy", "")),
                    str(item.get("velocity", "")),
                    str(item.get("heading", ""))
                ]) + "\n")

    if format == "csvfullest":
        output.write(separator.join([
            "Time", "Latitude", "Longitude", "Accuracy", "Altitude", "VerticalAccuracy", "Velocity", "Heading",
            "DetectedActivties", "UNKNOWN", "STILL", "TILTING", "ON_FOOT", "WALKING", "RUNNING", "IN_VEHICLE",
            "ON_BICYCLE", "IN_ROAD_VEHICLE", "IN_RAIL_VEHICLE", "IN_TWO_WHEELER_VEHICLE", "IN_FOUR_WHEELER_VEHICLE"
        ]) + "\n")
        for item in locations:
            if 'longitudeE7' in item and 'latitudeE7' in item:
                if item["latitudeE7"] > 1800000000:
                    item["latitudeE7"] = item["latitudeE7"] - 4294967296
                if item["longitudeE7"] > 1800000000:
                    item["longitudeE7"] = item["longitudeE7"] - 4294967296
                output.write(separator.join([
                    datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "%.8f" % (item["latitudeE7"] / 10000000),
                    "%.8f" % (item["longitudeE7"] / 10000000),
                    str(item.get("accuracy", "")),
                    str(item.get("altitude", "")),
                    str(item.get("verticalAccuracy", "")),
                    str(item.get("velocity", "")),
                    str(item.get("heading", ""))
                ]) + separator)
                if "activity" in item:
                    a = _read_activity(item["activity"])
                    output.write(separator.join([
                        str(len(a)),
                        str(a.get("UNKNOWN", "")),
                        str(a.get("STILL", "")),
                        str(a.get("TILTING", "")),
                        str(a.get("ON_FOOT", "")),
                        str(a.get("WALKING", "")),
                        str(a.get("RUNNING", "")),
                        str(a.get("IN_VEHICLE", "")),
                        str(a.get("ON_BICYCLE", "")),
                        str(a.get("IN_ROAD_VEHICLE", "")),
                        str(a.get("IN_RAIL_VEHICLE", "")),
                        str(a.get("IN_TWO_WHEELER_VEHICLE", "")),
                        str(a.get("IN_FOUR_WHEELER_VEHICLE", ""))
                    ]) + "\n")
                else:
                    output.write("0" + separator.join([""] * 13) + "\n")

    if format == "kml":
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
        output.write("  <Document>\n")
        output.write("    <name>Location History</name>\n")
        for item in locations:
            if 'longitudeE7' in item and 'latitudeE7' in item:
                if item["latitudeE7"] > 1800000000:
                    item["latitudeE7"] = item["latitudeE7"] - 4294967296
                if item["longitudeE7"] > 1800000000:
                    item["longitudeE7"] = item["longitudeE7"] - 4294967296
                output.write("    <Placemark>\n")
                # Order of these tags is important to make valid KML: TimeStamp, ExtendedData, then Point
                output.write("      <TimeStamp><when>")
                time = datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000)
                output.write(time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                output.write("</when></TimeStamp>\n")
                if "accuracy" in item or "speed" in item or "altitude" in item:
                    output.write("      <ExtendedData>\n")
                    if "accuracy" in item:
                        output.write("        <Data name=\"accuracy\">\n")
                        output.write("          <value>%d</value>\n" % item["accuracy"])
                        output.write("        </Data>\n")
                    if "speed" in item:
                        output.write("        <Data name=\"speed\">\n")
                        output.write("          <value>%d</value>\n" % item["speed"])
                        output.write("        </Data>\n")
                    if "altitude" in item:
                        output.write("        <Data name=\"altitude\">\n")
                        output.write("          <value>%d</value>\n" % item["altitude"])
                        output.write("        </Data>\n")
                    output.write("      </ExtendedData>\n")
                output.write(
                    "      <Point><coordinates>%s,%s</coordinates></Point>\n" %
                    (item["longitudeE7"] / 10000000, item["latitudeE7"] / 10000000)
                )
                output.write("    </Placemark>\n")
        output.write("  </Document>\n</kml>\n")

    if format == "gpx" or format == "gpxtracks":
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output.write("<gpx xmlns=\"http://www.topografix.com/GPX/1/1\" version=\"1.1\"")
        output.write(" creator=\"Google Latitude JSON Converter\"")
        output.write(" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"")
        output.write(" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1")
        output.write(" http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
        output.write("  <metadata>\n")
        output.write("    <name>Location History</name>\n")
        output.write("  </metadata>\n")

        if format == "gpx":
            for item in locations:
                if 'longitudeE7' in item and 'latitudeE7' in item:
                    if item["latitudeE7"] > 1800000000:
                        item["latitudeE7"] = item["latitudeE7"] - 4294967296
                    if item["longitudeE7"] > 1800000000:
                        item["longitudeE7"] = item["longitudeE7"] - 4294967296
                    output.write(
                        "  <wpt lat=\"%s\" lon=\"%s\">\n" %
                        (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000)
                    )
                    if "altitude" in item:
                        output.write("    <ele>%d</ele>\n" % item["altitude"])

                    time = datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000)
                    output.write("    <time>%s</time>\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    output.write("    <desc>%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
                    if "accuracy" in item or "speed" in item:
                        output.write(" (")
                        if "accuracy" in item:
                            output.write("Accuracy: %d" % item["accuracy"])
                        if "accuracy" in item and "speed" in item:
                            output.write(", ")
                        if "speed" in item:
                            output.write("Speed:%d" % item["speed"])
                        output.write(")")
                    output.write("</desc>\n")
                    output.write("  </wpt>\n")

        if format == "gpxtracks":
            output.write("  <trk>\n")
            output.write("    <trkseg>\n")
            lastloc = {}
            for item in locations:
                if 'longitudeE7' in item and 'latitudeE7' in item:
                    if item["latitudeE7"] > 1800000000:
                        item["latitudeE7"] = item["latitudeE7"] - 4294967296
                    if item["longitudeE7"] > 1800000000:
                        item["longitudeE7"] = item["longitudeE7"] - 4294967296
                    if 'timestampMs' in lastloc:
                        timedelta = abs((int(item['timestampMs']) - int(lastloc['timestampMs'])) / 1000 / 60)
                        distancedelta = _distance(
                            item['latitudeE7'] / 10000000,
                            item['longitudeE7'] / 10000000,
                            lastloc['latitudeE7'] / 10000000,
                            lastloc['longitudeE7'] / 10000000
                        )
                        if timedelta > 10 or distancedelta > 40:
                            # No points for 10 minutes or 40km in under 10m? Start a new track.
                            output.write("    </trkseg>\n")
                            output.write("  </trk>\n")
                            output.write("  <trk>\n")
                            output.write("    <trkseg>\n")

                    output.write(
                        "      <trkpt lat=\"%s\" lon=\"%s\">\n" %
                        (item["latitudeE7"] / 10000000, item["longitudeE7"] / 10000000)
                    )
                    if "altitude" in item:
                        output.write("        <ele>%d</ele>\n" % item["altitude"])
                    time = datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000)
                    output.write("        <time>%s</time>\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    if "accuracy" in item or "speed" in item:
                        output.write("        <desc>\n")
                        if "accuracy" in item:
                            output.write("          Accuracy: %d\n" % item["accuracy"])
                        if "speed" in item:
                            output.write("          Speed:%d\n" % item["speed"])
                        output.write("        </desc>\n")
                    output.write("      </trkpt>\n")
                    lastloc = item
            output.write("    </trkseg>\n")
            output.write("  </trk>\n")
        output.write("</gpx>\n")


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("input", help="Input File (JSON)")
    arg_parser.add_argument("output", help="Output File (will be overwritten!)")
    arg_parser.add_argument(
        "-f",
        "--format",
        choices=["kml", "json", "csv", "csvfull", "csvfullest", "js", "gpx", "gpxtracks"],
        default="kml",
        help="Format of the output"
    )
    arg_parser.add_argument(
        "-v",
        "--variable",
        default="locationJsonData",
        help="Variable name to be used for js output"
    )
    arg_parser.add_argument("-s", "--startdate", help="The Start Date - format YYYY-MM-DD (0h00)", type=_valid_date)
    arg_parser.add_argument("-e", "--enddate", help="The End Date - format YYYY-MM-DD (0h00)", type=_valid_date)
    arg_parser.add_argument("-c", "--chronological", help="Sort items in chronological order", action="store_true")
    arg_parser.add_argument(
        '-w', "--semicolon",
        help="Use semicolon instead of colon in CSV files", action="store_true"
    )
    arg_parser.add_argument("-i", "--iterative", help="Loads the JSON file iteratively", action="store_true")

    args = arg_parser.parse_args()

    if args.input == args.output:
        arg_parser.error("Input and output have to be different files")
        return

    if args.iterative:
        if not ijson_available:
            print("ijson is not available. Please install with `pip install ijson` and try again")
            return

        items = ijson.items(open(args.input, "r"), "locations.item")
    else:
        try:
            with open(args.input, "r") as f:
                json_data = f.read()
        except OSError as error:
            print("Error opening input file %s: %s" % (args.input, error))
            return
        except MemoryError:
            print("File too big, please use the -i parameter")
            return

        try:
            data = json.loads(json_data)
        except ValueError as error:
            print("Error decoding json: %s" % error)
            return

        items = data["locations"]

    try:
        f_out = open(args.output, "w")
    except OSError as error:
        print("Error creating output file for writing: %s" % error)
        return

    separator = ","
    if args.semicolon:
        separator = ";"

    convert(items, f_out, args.format, args.variable, args.startdate, args.enddate, args.chronological, separator)

    f_out.close()


if __name__ == "__main__":
    sys.exit(main())
