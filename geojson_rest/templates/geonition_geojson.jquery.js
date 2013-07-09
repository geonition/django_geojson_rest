{% load url from future %}
/*
 javascript functions for the geojson_rest app
*/
gnt.app_version.geojson_rest = '5.2.2';
gnt.geo = {};

/*
 This function queries features from the database that fit the
 given values.
 
 user -- the user the features belong to, also allowed: '@me', '@all'
 group -- the group the features belong to, also allowed: '@all', '@self'
 limit_params -- string starting with '?'
    parameters in the get limiting parameters:
    time -- the time the features was valid, also allowed '@now', '@all'

*/
gnt.geo.get_features =
function(user, group, limit_params, ajax_params) {
    if(limit_params == undefined) {
        limit_params = "";
    }
    if(ajax_params === undefined) {
        ajax_param = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'feat' %}/" + user + "/" + group + limit_params,
            type: "GET",
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );
    $.ajax(kwargs);
};

/*
 This function retreives only one feature from the database
 that fit the given user, group and feature_id.
 
 user -- the user the features belong to, also allowed: '@me', '@all'
 group -- the group the features belong to, also allowed: '@all', '@self'
 feature_id -- the id of the feature

*/
gnt.geo.get_feature =
function(user, group, feature_id, ajax_params) {
    if(limit_params == undefined) {
        limit_params = "";
    }
    if(ajax_params === undefined) {
        ajax_param = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'feat' %}/" + user + "/" + group + "/" + feature_id,
            type: "GET",
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );
    $.ajax(kwargs);
};

/*
 create_feature function saves a new feature, this function
 only saves one feature at the time. The function takes the
 following arguments:
 user -- the user that is saving the feature, '@me', '@all' reserved
 group -- the group the feature belongs to '@self', '@all' reserved
 feature -- geojson feature with additional parameters
 ajax_params -- possibility to extend the ajax call with this json
 
 The feature can have the following parameters:
 
 "type" -- always 'Feature' required
 "geometry" -- geojson geometry required
 "properties" -- json object required
 "id" -- will be overridden as this will create a new feature
 "private" -- tells if the feature is private or not, optional, default: true
 "time" -- time object (read only)
 "user" -- the owner of the feature (read only)
 "group" -- the group the feature belong to (read only)
 
*/
gnt.geo.create_feature =
function(user, group, feature, ajax_params) {

    var geojson_string = feature;
    if( typeof(" ") !== typeof(geojson_string)) {
        geojson_string = JSON.stringify(geojson_string);
    }
    if(ajax_params === undefined) {
        ajax_param = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'feat' %}/" + user + "/" + group,
            type: "POST",
            data: geojson_string,
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );
    $.ajax(kwargs);
};

/*
 update_feature, updates a feature with an id.
 All features in the collection should already have been saved
 once and should contain an id.
 
 user -- the user that the feature belong to
 group -- the group the feature belongs to
 feature -- the features to be updated (check create for params)
 ajax_params -- extra ajax params for ajax call
*/
gnt.geo.update_feature =
function(user, group, feature, ajax_params) {
    var geojson_string = feature;
    var feature_id = '';
    if( typeof(" ") !== typeof(geojson_string)) {
        feature_id = feature.id;
        geojson_string = JSON.stringify(geojson_string);
    } else {
        // need to get the id of the feature
        feature_id = JSON.parse(geojson_string).id;
    }
    if(ajax_params === undefined) {
        ajax_params = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'feat' %}/" + user + "/" + group + "/" + feature_id,
            type: "PUT",
            data: geojson_string,
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );

    $.ajax(kwargs);
};

/*
 delete_feature, deletes one feature
 the feature has to have an id set to be deleted.
*/
gnt.geo.delete_feature =
function(user, group, feature, ajax_params) {
    var geojson_string = feature;
    var feature_id = '';
    if( typeof(" ") !== typeof(geojson_string)) {
        feature_id = feature.id;
        geojson_string = JSON.stringify(geojson_string);
    } else {
        // need to get the id of the feature
        feature_id = JSON.parse(geojson_string).id;
    }
    if(ajax_params === undefined) {
        ajax_params = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'feat' %}/" + user + "/" + group + "/" + feature_id,
            type: "DELETE",
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );

    $.ajax(kwargs);
};

/*
 This function will create a property.
 
 user -- the user the property belongs to, defaults to @me
 group -- the group the property should be saved to defaults to @self
 feature_id -- id of the feature the created property should belong to
               if set as @null the property will not be connected to a feature
 property -- A JSON of the key value pairs to save
 ajax_params -- additional parameters to handle callbacks etc.
 
*/
gnt.geo.create_property = 
function(user, group, feature_id, property, ajax_params) {
    
    var json_string = property;
    
    if( typeof(" ") !== typeof(geojson_string)) {
        json_string = JSON.stringify(json_string);
    }
    
    if(ajax_params === undefined) {
        ajax_params = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    if(feature_id === undefined) {
        feature_id = '@null';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'prop' %}/" + user + "/" + group + "/" + feature_id,
            type: "POST",
            contentType: "application/json",
            dataType: "json",
            data: json_string,
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );

    $.ajax(kwargs);
};


/*
 This function will update a property.
 
 user -- the user the property belongs to, defaults to @me
 group -- the group the property should be saved to defaults to @self
 feature_id -- id of the feature the updated property should belong to
               if set as @null the property will not be connected to a feature
 property -- A JSON of the key value pairs to update, requires an id field
 ajax_params -- additional parameters to handle callbacks etc.
 
*/
gnt.geo.update_property = 
function(user, group, feature_id, property, ajax_params) {
    
    if( typeof(" ") !== typeof(geojson_string)) {
        property_id = property.id;
        json_string = JSON.stringify(property);
    } else {
        // need to get the id of the feature
        property_id = JSON.parse(property).id;
        json_string = property;
    }
    
    if(ajax_params === undefined) {
        ajax_params = {};
    }
    if(user === undefined) {
        user = '@me';
    }
    if(group === undefined) {
        group = '@self';
    }
    if(feature_id === undefined) {
        feature_id = '@null';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'prop' %}/" + user + "/" + group + "/" + feature_id + "/" + property_id,
            type: "PUT",
            contentType: "application/json",
            dataType: "json",
            data: json_string,
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );

    $.ajax(kwargs);
};

/*
This function gets properties.

 user -- the user the property belongs to, defaults to @all
 group -- the group the property should be queried from. defaults to @all
 feature_id -- id of the feature the updated property should belong to.
               if set as @null the property will not be connected to a feature
 property -- A JSON of the key value pairs to update, requires an id field
 ajax_params -- additional parameters to handle callbacks etc.

*/
gnt.geo.get_properties = function(user,
                                  group,
                                  feature_id,
                                  property_id,
                                  ajax_params) {
    
    if(ajax_params === undefined) {
        ajax_param = {};
    }
    
    if(user === undefined) {
        user = '@all';
    }
    if(group === undefined) {
        group = '@all';
    }
    if(feature_id === undefined) {
        feature_id = '@all';
    }
    if(property_id === undefined) {
        property_id = '@all';
    }
    
    var kwargs = $.extend(
        ajax_params,
        {
            url: "{% url 'prop' %}/" + user + "/" + group + "/" + feature_id + "/" + property_id,
            type: "GET",
            contentType: "application/json",
            dataType: "json",
            beforeSend: function(xhr) {
                xhr.withCredentials = true;
            }
        }
    );
    $.ajax(kwargs);
};
