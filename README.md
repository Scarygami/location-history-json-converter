# Location History JSON Converter

This Python script takes the JSON file of your location history which you can get via [Google Takeout](https://www.google.com/takeout/?pli=1#custom:latitude) and converts it into other formats.

You will need to have Python installed and know a little bit about running scripts from the command line.

### Usage
```
location_history_json_converter.py inputFileName [-o] [-h] [-f {kml,json,csv,js,gpx,gpxtracks}] [-v]

input                Input File (JSON)

optional arguments:
  -o, --output                                  Name of the output file (will be overwritten without prompt!) if left unspecified, the output file name will default to replacing the input file name's extension
  -h, --help                                    Show this help message and exit
  -f, --format {kml,json,csv,js,gpx,gpxtracks}  Format of the output
  -v, --variable                                Variable name for js export
```

### Available formats

##### kml (default)
KML file with placemarks for each location in your Location History.  Each placemark will have a location, a timestamp, and accuracy/speed/altitude as available.  Data produced is valid KML 2.2.

##### csv
Comma-separated text file with a timestamp field and a location field, suitable for upload to Fusion Tables.

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

### Licence

```
Copyright 2012-2013 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
