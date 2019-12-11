# Location History JSON Converter

This Python script takes the JSON file of your location history which you can get via
[Google Takeout](https://takeout.google.com/settings/takeout/custom/location_history)
and converts it into other formats.

### Requirements

*  [Install python](https://wiki.python.org/moin/BeginnersGuide/Download) (2.7+/3.2+) if you don't have it installed already.

*  Download the python script by either cloning this repository
   (`git clone https://github.com/Scarygami/location-history-json-converter`)
   or [downloading the script file](https://raw.githubusercontent.com/Scarygami/location-history-json-converter/master/location_history_json_converter.py).

*  Request your location history via [Google Takeout](https://takeout.google.com/settings/takeout/custom/location_history)
   and once the package is ready, download and unzip it.

   I find it easiest to place the `Location History.json` in the same folder where the script is located.

### Usage
```
python location_history_json_converter.py input output [-h] [-f {format, see below}]

input                Input File (Location History.json)
output               Output File (will be overwritten!)

optional arguments:
  -h, --help                             Show this help message and exit
  -f, --format {format, see below}       Format of the output
  -i, --iterative                        Loads the JSON file iteratively
  -s, --startdate STARTDATE              The Start Date - format YYYY-MM-DD (0h00)
  -e, --enddate ENDDATE                  The End Date - format YYYY-MM-DD (0h00)
  -a, --accuracy ACCURACY                Maximum Accuracy (in meters), lower is better
  -c, --chronological                    Sort items in chronological order
  -v, --variable VARIABLE                Variable name for js export
      --separator SEPARATOR              Separator to be used for CSV formats, defaults to comma
  -p, --polygon [lat,lon [lat,lon ...]]  List of points (lat, lon) that create a polygon.
                                         If two points are given a rectangle is created.
```

### Special requirements for some options

#### `-i, --iterative`

The iterative parsing mode is achieved using the [ijson](https://pypi.org/project/ijson/).

To be able to use this option you will have to install it with

    pip install ijson

#### `-p, --polygon`

Using this option you can specify a list of coordinates to define a polygon,
and only locations that are in this polygon will be added to the output file.

E.g `-p 43.665,10.334 43.815,10.492` to only include locations in the rectangle
defined by the two corner points.

If you have negative latitudes you will need to but the coordinate in quotes
with an extra space before the minus sign, so that `argparse` can detect read
the arguments correctly.

    --polygon 20,-70 " -20,-50"

The polygon filtering is achieved using [Shapely](https://pypi.org/project/Shapely/).

To be able to use this option you will have to install it with

    pip install Shapely

On Windows this command will most likely fail. Instead you can download a wheel
that matches your OS and Python Version from https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely

You can then install Shapely using this command:

    python -m pip install Shapely-X-cpX-cpXm-winX.whl


### Available formats

#### kml (default)
KML file with placemarks for each location in your Location History.
Each placemark will have a location, a timestamp, and accuracy/speed/altitude as available.
Data produced is valid KML 2.2.

#### csv
Comma-separated text file with a timestamp field and a location field, suitable for upload to Fusion Tables.

#### csvfull
Comma-separated text file with all location information, excluding activities

#### csvfullest
Comma-separated text file with all location information, including activities

#### json
Smaller JSON file with only the timestamp and the location.

#### js
JavaScript file which sets a variable in global namespace (default: window.locationJsonData)
to the full data object for easy access in local scripts.
Just include the js file before your actual script.
Only timestamp and location are included.

#### jsonfull, jsfull
These types essentially make a full copy of the entries in the original JSON File in json or js format.
With the option of filtering start and end date this can be used to create a smaller file in iterative mode,
that can then be handled without iterative mode (necessary for gpxtracks and the chronological option).

#### gpx
GPS Exchange Format including location, timestamp, and accuracy/speed/altitude as available.
Data produced is valid GPX 1.1.  Points are stored as individual, unrelated waypoints (like the other formats, except for gpxtracks).

#### gpxtracks
GPS Exchange Format including location, timestamp, and accuracy/speed/altitude as available.
Data produced is valid GPX 1.1.  Points are grouped together into tracks by time and location (specifically, two chronological points split a track if they differ by over 10 minutes or approximately 40 kilometers).
