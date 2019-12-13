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

try:
    from shapely.geometry import Point, Polygon
except ImportError:
    shapely_available = False
else:
    shapely_available = True


def _valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise ArgumentTypeError(msg)


def _valid_polygon(s):
    try:
        [lat, lon] = s.split(",")
        return float(lat), float(lon)
    except ValueError:
        msg = "Not a valid point: '{0}'.".format(s)
        raise ArgumentTypeError(msg)


def _check_point(polygon, lat, lon):
    """Returns true if the point specified by lat and lon is inside the polygon"""
    point = Point(lat / 10000000, lon / 10000000)
    return polygon.contains(point)


def _read_activity(arr):
    ret = {}
    if len(arr) == 1 and "activity" in arr[0]:
        items = arr[0]["activity"]
        for item in items:
            if "type" in item and "confidence" in item:
                ret[item["type"]] = item["confidence"]
    return ret


def _distance(lat1, lon1, lat2, lon2):
    """Returns the distance between to two coordinates in km using the Haversine formula"""

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


def _write_header(output, format, js_variable, separator):
    """Writes the file header for the specified format to output"""

    if format == "json" or format == "js" or format == "jsonfull" or format == "jsfull":
        if format == "js" or format == "jsfull":
            output.write("window.%s = " % js_variable)
        output.write("{\"locations\":[")
        return

    if format == "csv":
        output.write(separator.join(["Time", "Latitude", "Longitude"]) + "\n")
        return

    if format == "csvfull":
        output.write(separator.join([
            "Time", "Latitude", "Longitude", "Accuracy", "Altitude", "VerticalAccuracy", "Velocity", "Heading"
        ]) + "\n")
        return

    if format == "csvfullest":
        output.write(separator.join([
            "Time", "Latitude", "Longitude", "Accuracy", "Altitude", "VerticalAccuracy", "Velocity", "Heading",
            "DetectedActivties", "UNKNOWN", "STILL", "TILTING", "ON_FOOT", "WALKING", "RUNNING", "IN_VEHICLE",
            "ON_BICYCLE", "IN_ROAD_VEHICLE", "IN_RAIL_VEHICLE", "IN_TWO_WHEELER_VEHICLE", "IN_FOUR_WHEELER_VEHICLE"
        ]) + "\n")
        return

    if format == "kml":
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
        output.write("  <Document>\n")
        output.write("    <name>Location History</name>\n")
        return

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
        return


def _write_location(output, format, location, separator, first, last_location):
    """Writes the data for one location to output according to specified format"""

    if format == "json" or format == "js":
        if not first:
            output.write(",")

        item = {
            "timestampMs": location["timestampMs"],
            "latitudeE7": location["latitudeE7"],
            "longitudeE7": location["longitudeE7"]
        }
        output.write(json.dumps(item, separators=(',', ':')))
        return

    if format == "jsonfull" or format == "jsfull":
        if not first:
            output.write(",")

        output.write(json.dumps(location, separators=(',', ':')))
        return

    if format == "csv":
        output.write(separator.join([
            datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "%.8f" % (location["latitudeE7"] / 10000000),
            "%.8f" % (location["longitudeE7"] / 10000000)
        ]) + "\n")

    if format == "csvfull":
        output.write(separator.join([
            datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "%.8f" % (location["latitudeE7"] / 10000000),
            "%.8f" % (location["longitudeE7"] / 10000000),
            str(location.get("accuracy", "")),
            str(location.get("altitude", "")),
            str(location.get("verticalAccuracy", "")),
            str(location.get("velocity", "")),
            str(location.get("heading", ""))
        ]) + "\n")

    if format == "csvfullest":
        output.write(separator.join([
            datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "%.8f" % (location["latitudeE7"] / 10000000),
            "%.8f" % (location["longitudeE7"] / 10000000),
            str(location.get("accuracy", "")),
            str(location.get("altitude", "")),
            str(location.get("verticalAccuracy", "")),
            str(location.get("velocity", "")),
            str(location.get("heading", ""))
        ]) + separator)
        if "activity" in location:
            a = _read_activity(location["activity"])
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
        output.write("    <Placemark>\n")

        # Order of these tags is important to make valid KML: TimeStamp, ExtendedData, then Point
        output.write("      <TimeStamp><when>")
        time = datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000)
        output.write(time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        output.write("</when></TimeStamp>\n")
        if "accuracy" in location or "speed" in location or "altitude" in location:
            output.write("      <ExtendedData>\n")
            if "accuracy" in location:
                output.write("        <Data name=\"accuracy\">\n")
                output.write("          <value>%d</value>\n" % location["accuracy"])
                output.write("        </Data>\n")
            if "speed" in location:
                output.write("        <Data name=\"speed\">\n")
                output.write("          <value>%d</value>\n" % location["speed"])
                output.write("        </Data>\n")
            if "altitude" in location:
                output.write("        <Data name=\"altitude\">\n")
                output.write("          <value>%d</value>\n" % location["altitude"])
                output.write("        </Data>\n")
            output.write("      </ExtendedData>\n")
        output.write(
            "      <Point><coordinates>%s,%s</coordinates></Point>\n" %
            (location["longitudeE7"] / 10000000, location["latitudeE7"] / 10000000)
        )

        output.write("    </Placemark>\n")

    if format == "gpx":
        output.write(
            "  <wpt lat=\"%s\" lon=\"%s\">\n" %
            (location["latitudeE7"] / 10000000, location["longitudeE7"] / 10000000)
        )
        if "altitude" in location:
            output.write("    <ele>%d</ele>\n" % location["altitude"])

        time = datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000)
        output.write("    <time>%s</time>\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        output.write("    <desc>%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        if "accuracy" in location or "speed" in location:
            output.write(" (")
            if "accuracy" in location:
                output.write("Accuracy: %d" % location["accuracy"])
            if "accuracy" in location and "speed" in location:
                output.write(", ")
            if "speed" in location:
                output.write("Speed:%d" % location["speed"])
            output.write(")")
        output.write("</desc>\n")
        output.write("  </wpt>\n")

    if format == "gpxtracks":
        if first:
            output.write("  <trk>\n")
            output.write("    <trkseg>\n")

        if last_location:
            timedelta = abs((int(location['timestampMs']) - int(last_location['timestampMs'])) / 1000 / 60)
            distancedelta = _distance(
                location['latitudeE7'] / 10000000,
                location['longitudeE7'] / 10000000,
                last_location['latitudeE7'] / 10000000,
                last_location['longitudeE7'] / 10000000
            )
            if timedelta > 10 or distancedelta > 40:
                # No points for 10 minutes or 40km in under 10m? Start a new track.
                output.write("    </trkseg>\n")
                output.write("  </trk>\n")
                output.write("  <trk>\n")
                output.write("    <trkseg>\n")

        output.write(
            "      <trkpt lat=\"%s\" lon=\"%s\">\n" %
            (location["latitudeE7"] / 10000000, location["longitudeE7"] / 10000000)
        )

        if "altitude" in location:
            output.write("        <ele>%d</ele>\n" % location["altitude"])
        time = datetime.utcfromtimestamp(int(location["timestampMs"]) / 1000)
        output.write("        <time>%s</time>\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if "accuracy" in location or "speed" in location:
            output.write("        <desc>\n")
            if "accuracy" in location:
                output.write("          Accuracy: %d\n" % location["accuracy"])
            if "speed" in location:
                output.write("          Speed:%d\n" % location["speed"])
            output.write("        </desc>\n")
        output.write("      </trkpt>\n")


def _write_footer(output, format):
    """Writes the file footer for the specified format to output"""

    if format == "json" or format == "js" or format == "jsonfull" or format == "jsfull":
        output.write("]}")
        if format == "js" or format == "jsfull":
            output.write(";")
        return

    if format == "kml":
        output.write("  </Document>\n</kml>\n")
        return

    if format == "gpx" or format == "gpxtracks":
        if format == "gpxtracks":
            output.write("    </trkseg>\n")
            output.write("  </trk>\n")
        output.write("</gpx>\n")
        return


def convert(locations, output, format="kml",
            js_variable="locationJsonData", separator=",",
            start_date=None, end_date=None, accuracy=None, polygon=None,
            chronological=False):
    """Converts the provided locations to the specified format

    Parameters
    ----------

    locations : Iterable
        list or other Iterable of locations from Google Takeout JSON file

    output: File or StringIO or similar
        All output will be written to this buffer

    format: str
        Format to convert to
        Can be one of "kml", "json", "js", "jsonfull", "jsfull", "csv", "csvfull", "csvfullest", "gpx", "gpxtracks"
        See README.md for details about those formats

    js_variable: str
        Variable name to be used for js output

    separator: str
        What separator to use for the csv formats

    start_date: datetime
        Locations before this date will be ignored

    end_date: datetime
        Locations after this date will be ignored

    accuracy: int
        Locations with a higher accuracy value (i.e. worse accuracy) will be ignored

    polygon: shapely.Polygon
        All locations outside of the Polygon will be ignored

    chronological: bool
        Whether to sort all timestamps in chronological order (required for gpxtracks)
        This might be uncessary since recent Takeout data seems properly sorted already.
    """

    if chronological:
        locations = sorted(locations, key=lambda item: item["timestampMs"])

    _write_header(output, format, js_variable, separator)

    first = True
    last_loc = None
    added = 0
    print("Progress:")
    for item in locations:
        if "longitudeE7" not in item or "latitudeE7" not in item or "timestampMs" not in item:
            continue

        time = datetime.utcfromtimestamp(int(item["timestampMs"]) / 1000)
        print("\r%s / Locations written: %s" % (time.strftime("%Y-%m-%d %H:%M"), added), end="")

        if "accuracy" in item and item["accuracy"] > accuracy:
            continue

        if start_date and start_date > time:
            continue
        if end_date and end_date < time:
            if chronological:
                # If locations are sorted and we are past the enddate there are no further locations to be expected
                # This could probably be the default behavior
                break
            continue

        if polygon and not _check_point(polygon, item["latitudeE7"], item["longitudeE7"]):
            continue

        # Fix overflows in Google Takeout data:
        # https://gis.stackexchange.com/questions/318918/latitude-and-longitude-values-in-google-takeout-location-history-data-sometimes
        if item["latitudeE7"] > 1800000000:
            item["latitudeE7"] = item["latitudeE7"] - 4294967296
        if item["longitudeE7"] > 1800000000:
            item["longitudeE7"] = item["longitudeE7"] - 4294967296

        _write_location(output, format, item, separator, first, last_loc)

        if first:
            first = False
        last_loc = item
        added = added + 1

    _write_footer(output, format)
    print("")


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("input", help="Input File (Location History.json)")
    arg_parser.add_argument("output", help="Output File (will be overwritten!)")

    arg_parser.add_argument(
        "-f",
        "--format",
        choices=["kml", "json", "js", "jsonfull", "jsfull", "csv", "csvfull", "csvfullest", "gpx", "gpxtracks"],
        default="kml",
        help="Format of the output"
    )

    arg_parser.add_argument(
        "-i", "--iterative",
        help="Loads the JSON file iteratively, to be able to handle bigger files",
        action="store_true"
    )

    arg_parser.add_argument("-s", "--startdate", help="The Start Date - format YYYY-MM-DD (0h00)", type=_valid_date)
    arg_parser.add_argument("-e", "--enddate", help="The End Date - format YYYY-MM-DD (0h00)", type=_valid_date)
    arg_parser.add_argument("-a", "--accuracy", help="Maximum accuracy (in meters), lower is better.", type=int)

    arg_parser.add_argument(
        "-c", "--chronological",
        help="Sort items in chronological order (might be unnessary)",
        action="store_true"
    )

    arg_parser.add_argument(
        "-v", "--variable",
        default="locationJsonData",
        help="Variable name to be used for js output"
    )

    arg_parser.add_argument(
        "--separator",
        default=",",
        help="Separator to be used for CSV formats, defaults to comma"
    )

    arg_parser.add_argument(
        '-p', "--polygon",
        help="List of points (lat, lon) that create a polygon. " +
             "If two points are given a rectangle is created.",
        metavar="lat,lon",
        nargs='*',
        type=_valid_polygon
    )

    args = arg_parser.parse_args()

    if args.input == args.output:
        arg_parser.error("Input and output have to be different files")
        return

    if args.polygon and len(args.polygon) < 2:
        arg_parser.error("Polygon needs at least 2 points to create a rectangule (bottom left and top right)")
        return

    polygon = None
    if args.polygon:
        if not shapely_available:
            print("shapely is not available. Please install with `pip install shapely` and try again.")
            return

        if len(args.polygon) == 2:
            point1, point2 = args.polygon
            lat1, lon1 = point1
            lat2, lon2 = point2
            ext = [
                (float(min(lat1, lat2)), float(min(lon1, lon2))),
                (float(max(lat1, lat2)), float(min(lon1, lon2))),
                (float(max(lat1, lat2)), float(max(lon1, lon2))),
                (float(min(lat1, lat2)), float(max(lon1, lon2)))
            ]
        else:
            ext = [(elem.split(",")[0], elem.split(",")[1]) for elem in args.polygon]

        polygon = Polygon(ext)

    if args.iterative:
        if args.chronological:
            print("-----------------------------------")
            print("Please note that iterative mode doesn't really work when chronological is activated,")
            print("since all locations need to be fetched first to be able to sort them.")
            print("The setting might also be unnessary since recent Google Takeout data already seems properly sorted.")
            print("")
            print("If you need to use this setting you can instead create a smaller JSON file")
            print("using jsonfull format with filters for start date, end date and accuracy in iterative mode:")
            print("")
            print("%s %s small.json -f jsonfull -i -s YYYY-MM-DD -e YYYY-MM-DD -a ACCURACY" % (sys.argv[0], args.input))
            print("")
            print("You can then use the generated smaller JSON file with --chronological but without --iterative")
            print("")
            print("%s small.json %s -f %s -c" % (sys.argv[0], args.output, args.format))
            print("")
            print("---------------------------------------------------------------------------------------------")
            print("")
            answer = input("Do you want to continue anyway (y/N)? ").upper()
            if answer != "Y" and answer != "YES":
                return

        if not ijson_available:
            print("ijson is not available. Please install with `pip install ijson` and try again.")
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

    if args.enddate:
        args.enddate = args.enddate.replace(hour=23, minute=59, second=59, microsecond=999999)

    convert(
        items, f_out,
        format=args.format,
        js_variable=args.variable,
        start_date=args.startdate,
        end_date=args.enddate,
        accuracy=args.accuracy,
        polygon=polygon,
        chronological=args.chronological
    )

    f_out.close()


if __name__ == "__main__":
    sys.exit(main())
