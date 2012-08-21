"""
This file contains admin actions used by the geojson_rest application
"""
import csv
import json
import types
from django.contrib.gis.geos import GEOSGeometry
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _


def download_csv(modeladmin, request, queryset):
    """
    This action will modify the queryset objects into
    csv for downloading. The queryset objects is required
    to have their own .to_json() function which will provide
    the json representation of that object.
    
    Special reserved values include
    geometry - should represent a geojson geometry otherwise skipped
    """
    #make the response object to write to
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % str(modeladmin)
    
    #create a csv writer
    writer = csv.writer(response)
    
    #create a json list of the queryset objects
    dict_list = [obj.to_json() for obj in queryset]
    
    #selector list is the header of the csv file
    selector_list = get_selectors(dict_list)
    writer.writerow(selector_list)
    
    for dict_json in dict_list:
        
        value = dict_json
        values = []
        for selector in selector_list:
            
            #handle the geometry geojson and present it as WKT
            if selector == 'geometry':
                value = GEOSGeometry(json.dumps(value[selector])).wkt
            else:   
                split_selector = selector.split('.')
            
                for part_selector in split_selector:
                    try:
                        value = value[part_selector]
                    except KeyError:
                        value = u''
                
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
            
            if key != 'geometry' and type(obj[key]) == types.DictType:
                subkeys = get_selectors([obj[key]])
                for subkey in subkeys:
                    subkey_selector = "%s.%s" % (key_selector, subkey)
                    
                    if subkey_selector not in key_selectors:
                        key_selectors.append(subkey_selector)
                    
            elif key_selector not in key_selectors:
                key_selectors.append(key_selector)
                
    return key_selectors