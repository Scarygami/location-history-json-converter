# Location History JSON Converter

This Python script takes the JSON file of your location history which you can get via
[Google Takeout](https://takeout.google.com/settings/takeout/custom/location_history)
and converts it into other formats.

You will need to have Python installed and know a little bit about running scripts from the command line.

### Usage
```
location_history_json_converter.py input output [-h] [-f {kml,json,csv,csvfull,csvfullest,js,gpx,gpxtracks}]

input                Input File (JSON)
output               Output File (will be overwritten!)

optional arguments:
  -h, --help                                                       Show this help message and exit
  -f, --format {kml,json,csv,csvfull,csvfullest,js,gpx,gpxtracks}  Format of the output
  -v, --variable                                                   Variable name for js export
  -s, --startdate STARTDATE                                        The Start Date - format YYYY-MM-DD (0h00)
  -e, --enddate ENDDATE                                            The End Date - format YYYY-MM-DD (0h00)
  -c, --chronological                                              Sort items in chronological order

```

### Available formats

##### kml (default)
KML file with placemarks for each location in your Location History.  Each placemark will have a location, a timestamp, and accuracy/speed/altitude as available.  Data produced is valid KML 2.2.

##### csv
Comma-separated text file with a timestamp field and a location field, suitable for upload to Fusion Tables.

##### csvfull
Comma-separated text file with all location information, excluding activities

##### csvfullest
Comma-separated text file with all location information, including activities

##### json
Smaller JSON file with only the timestamp and the location.

##### js
JavaScript file which sets a variable in global namespace (default: window.locationJsonData)
to the full data object for easy access in local scripts.
Just include the js file before your actual script.
Only timestamp and location are included.

##### gpx
GPS Exchange Format including location, timestamp, and accuracy/speed/altitude as available.
Data produced is valid GPX 1.1.  Points are stored as individual, unrelated waypoints (like the other formats, except for gpxtracks).

##### gpxtracks
GPS Exchange Format including location, timestamp, and accuracy/speed/altitude as available.
Data produced is valid GPX 1.1.  Points are grouped together into tracks by time and location (specifically, two chronological points split a track if they differ by over 10 minutes or approximately 40 kilometers).
