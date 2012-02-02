/*
 javascript functions for the geojson_rest app
*/
gnt.app_version['geojson_rest'] = '2.0.0';
gnt['geo'] = {};

/*
gnt.geo.get_features retrieves features according to the limiting params

the limit_params is a GET string starting with a "?"

reserved keys for the limiting parameter include the
following:

user_id = id of user
time = time when the feature was valid

*/
gnt.geo['get_features'] =
function(limit_params, callback_function) {
    if(limit_params == undefined) {
        limit_params = "";
    }

    $.ajax({
        url: "{% url api_feature %}" + limit_params,
        type: "GET",
        contentType: "application/json",
        success: function(data) {
            if(callback_function !== undefined) {
                callback_function(data);
                }
            },
        error: function(e) {
            if(callback_function !== undefined) {
                callback_function(e);
            }
        },
        dataType: "json",
        beforeSend: function(xhr) {
            xhr.withCredentials = true;
        }
    });
};

/*
 create_feature function saves a new feature of features from a feature
 collection to the database
*/
gnt.geo['create_feature'] =
function(feature_or_feature_collection, callback_function) {
    $.ajax({
        url: "{% url api_feature %}",
        type: "POST",
        data: JSON.stringify(feature_or_feature_collection),
        contentType: "application/json",
        success: function(data) {
            if(callback_function !== undefined) {
                callback_function(data);
            }
        },
        error: function(e) {
            if(callback_function !== undefined) {
                callback_function(e);
            }
        },
        dataType: "json",
        beforeSend: function(xhr) {
            xhr.withCredentials = true;
        }
    });
};

/*
 update_feature, updates a feature with and id or a set of
 features in a featurecollection. All features in the collection
 should already have been saved once and should contain an id.
*/
gnt.geo['update_feature'] =
function(feature_or_feature_collection, callback_function) {
    $.ajax({
        url: "{% url api_feature %}",
        type: "PUT",
        data: JSON.stringify(feature_or_feature_collection),
        contentType: "application/json",
        success: function(data) {
            if(callback_function) {
                callback_function(data);
            }
        },
        error: function(e) {
            if(callback_function) {
                callback_function(e);
            }
        },
        dataType: "json",
        beforeSend: function(xhr) {
            xhr.withCredentials = true;
        }
    });
};

/*
 delete_feature, deletes the feature(s) with the given feature_id(s)
*/
gnt.geo['delete_feature'] =
function(feature_or_feature_collection, callback_function) {
    /*
    ensure the backwords compatibility
    New logic expects an array of ids
    If just one id is sent make it an array of length one
    */
    var feature_ids_array = [];
    var type = feature_or_feature_collection.type;
    var i = 0;

    if (type === "Feature"){
        feature_ids_array[0] = feature_or_feature_collection.id;
    }
    else if (type === "FeatureCollection") {
        for(i = 0; i < feature_or_feature_collection.features.length; i++){
            if (feature_or_feature_collection.features[i].id !== undefined){
                feature_ids_array.push(feature_or_feature_collection.features[i].id);
            }
        }
    }

    $.ajax({
        url: "{% url api_feature %}?ids=" + JSON.stringify(feature_ids_array),
        type: "DELETE",
        success: function(data) {
            if(callback_function) {
                callback_function(data);
            }
        },
        error: function(e) {
            if(callback_function) {
                callback_function(e);
            }
        },
        dataType: "json",
        beforeSend: function(xhr) {
            xhr.withCredentials = true;
        }
    });
};

