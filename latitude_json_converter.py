#!/usr/bin/env python

import sys
import json
from argparse import ArgumentParser
from datetime import datetime


def main(argv):
    arg_parser = ArgumentParser()
    arg_parser.add_argument("input", help="Input File (JSON)")
    arg_parser.add_argument("output", help="Output File (will be overwritten!)")
    arg_parser.add_argument("-f", action="store", dest="format", choices=["kml", "json", "csv"], default="kml", help="Format of the output")
    args = arg_parser.parse_args()
    if args.input == args.output:
        arg_parser.error("Input and output have to be different files")
        return

    try:
        json_data = open(args.input).read()
    except:
        print("Error opening input file")
        return

    # turn json_data into correct json
    json_data = "[" + json_data[1:-1] + "]"
    json_data = json_data.replace("\"data\" :", "")

    try:
        data = json.loads(json_data)
    except:
        print("Error decoding json")
        return

    if len("data") > 0:
        try:
            f_out = open(args.output, "w")
        except:
            print("Error creating output file for writing")
            return

        if args.format == "json":
            f_out.write("{\n")
            f_out.write("  \"data\": {\n")
            f_out.write("    \"items\": [\n")
            first = True
            for d in data:
                if "items" in d:
                    items = d["items"]
                    for item in items:
                        if first:
                            first = False
                        else:
                            f_out.write(",\n")
                        f_out.write("      {\n")
                        f_out.write("         \"timestampMs\": %s,\n" % item["timestampMs"])
                        f_out.write("         \"latitude\": %s,\n" % item["latitude"])
                        f_out.write("         \"longitude\": %s\n" % item["longitude"])
                        f_out.write("      }")
            f_out.write("\n    ]\n")
            f_out.write("  }\n}")

        if args.format == "csv":
            f_out.write("Time,Location\n")
            for d in data:
                if "items" in d:
                    items = d["items"]
                    for item in items:
                        f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
                        f_out.write(",")
                        f_out.write("%s %s\n" % (item["latitude"], item["longitude"]))

        if args.format == "kml":
            f_out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f_out.write("<kml xmlns=\"http://earth.google.com/kml/2.2\">\n")
            f_out.write("  <Document>\n")
            f_out.write("    <name>Location History</name>\n")
            for d in data:
                if "items" in d:
                    items = d["items"]
                    for item in items:
                        f_out.write("    <Placemark>\n")
                        f_out.write("      <Point><coordinates>%s,%s</coordinates></Point>\n" % (item["longitude"], item["latitude"]))
                        f_out.write("      <TimeStamp><when>")
                        f_out.write(datetime.fromtimestamp(int(item["timestampMs"]) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ"))
                        f_out.write("</when></TimeStamp>\n")
                        f_out.write("    </Placemark>\n")
            f_out.write("  </Document>\n</kml>\n")

        f_out.close()

    else:
        print("No data found in json")
        return


if __name__ == "__main__":
    sys.exit(main(sys.argv))
