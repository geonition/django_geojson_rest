"""
This file contains admin actions used by the geojson_rest application
"""
import csv
import json
import types
from django.contrib.gis.geos import GEOSGeometry
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from shapely.geometry import asShape

def download_csv(modeladmin, request, queryset):
    """
    This action will modify the queryset objects into
    csv for downloading. The queryset objects is required
    to have their own .to_json() function which will provide
    the json representation of that object.

    Special reserved values include
    geometry - should represent a geojson geometry otherwise skipped
    """
    srid = None
    if len(queryset) > 0 and hasattr(queryset[0], 'geometry'):
        srid = queryset[0].geometry.srid
#    else:
#        srid = getattr(settings, "SPATIAL_REFERENCE_SYSTEM_ID", 4326)

    #make the response object to write to
    response = HttpResponse(mimetype='text/csv')
    if srid is not None:
        response['Content-Disposition'] = 'attachment; filename={0}_{1}.csv'.format(modeladmin, srid)
    else:
        response['Content-Disposition'] = 'attachment; filename={0}.csv'.format(modeladmin)

    #create a csv writer
    writer = csv.writer(response)

    #create a json list of the queryset objects
    dict_list = [obj.to_json() for obj in queryset]

    #selector list is the header of the csv file
    selector_list = get_selectors(dict_list)
    # change column name 'geometry' to 'wkt' in csv header
    csv_header = ['wkt' if x == 'geometry' else x for x in selector_list]
    writer.writerow(csv_header)

    for dict_json in dict_list:

        value = dict_json
        values = []
        for selector in selector_list:

            #handle the geometry geojson and present it as WKT
            if selector == 'geometry':
#                value = GEOSGeometry(json.dumps(value[selector])).wkt
                # All geometry from/to_json functions in GeoDjango use
                # gdal and from_json has some problems. We use Shapely instead.
                value = asShape(value[selector]).to_wkt()
            else:
                split_selector = selector.split('.')
                #print("selector:" + selector)
                for part_selector in split_selector:
                    try:
                        value = value[unicode(part_selector, 'utf-8')]
                    except KeyError:
                        value = u''
                        break

            values.append(unicode(value).encode('utf-8'))
            value = dict_json

        writer.writerow(values)
        values = []

    return response

download_csv.short_description = _(u'Download as a csv file')

def get_selectors(json_list):
    """
    This function takes a list of dictionaries and
    calculates the keys to query all the values.

    Special reserved values include
    geometry - should represent a geojson geometry otherwise skipped
    """
    key_selectors = []

    for obj in json_list:
        keys = obj.keys()
        for key in keys:

            key_selector = "%s" % key
            key_selector = unicode(key_selector).encode('utf-8')

            if key != 'geometry' and type(obj[key]) == types.DictType:
                subkeys = get_selectors([obj[key]])
                for subkey in subkeys:
                    subkey_selector = "%s.%s" % (key_selector, subkey)
                    if type(subkey_selector) == str:
                        subkey_selector = unicode(subkey_selector, 'utf-8').encode('utf-8')
                    else:
                        subkey_selector = unicode(subkey_selector).encode('utf-8')

                    if subkey_selector not in key_selectors:
                        key_selectors.append(subkey_selector)

            elif key_selector not in key_selectors:
                key_selectors.append(key_selector)

    return key_selectors