/*
get_features retrieves features according to the limiting params

the limit_params is a GET string starting with a "?"

reserved keys for the limiting parameter include the
following:

user_id = id of user
time = time when the feature was valid

*/
function get_features(limit_params, callback_function) {
    
    if(limit_params === undefined) {
        limit_params = "";
    }
    
    dojo.xhrGet({
        "url": api_full_url + '{% url api_feature %}' + limit_params,
        "handleAs": "json",
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"response": response,
                                  "ioArgs": ioArgs});
            }
        }
    }); 
}

/*
 create_feature function saves a new feature of features from a feature
 collection to the database
*/
function create_feature(feature_or_feature_collection, callback_function) {
    dojo.xhrPost({
        "url": api_full_url + "{% url api_feature %}",
        "handleAs": "json",
        "postData": encodeURIComponent(dojo.toJson(feature_or_feature_collection)),
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"response": response,
                                  "ioArgs": ioArgs});
            }
        }
    });
}

/*
 update_feature, updates a feature with and id or a set of
 features in a featurecollection. All features in the collection
 should already have been saved once and should contain an id.
*/
function update_feature(feature_or_feature_collection, callback_function) {
    dojo.xhrPut({
        "url": api_full_url + "{% url api_feature %}",
        "handleAs": "text",
        "postData": encodeURIComponent(dojo.toJson(feature_or_feature_collection)),
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"response": response,
                                  "ioArgs": ioArgs});
            }
        }
    });
}

/*
 delete_feature, deletes the feature(s) with the given feature_id(s)
*/
function delete_feature(feature_or_feature_collection, callback_function) {
    
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



    dojo.xhrDelete({
        "url": api_full_url + '{% url api_feature %}?ids='+ dojo.toJson(feature_ids_array),
        "handleAs": "text",
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name )},
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"response": response,
                                  "ioArgs": ioArgs});
            }
        }
    });   
}


/*
 THE FUNCTIONS BELOW IS DEPRACATED AND SHOULD NOT BE USED
 THEY ARE TO BE REMOVED BUT IT IS NOT DEFINED WHEN..
*/
/*
This function saves the graphic given in GeoJSON format.

It takes as parameters:
graphic - a graphic in ESRI JSON notation

Brings functionality to handle differences with ESRI JSON
and GeoJSON
*/

function save_graphic(graphic, callback_function) {
    console.log("DEPRACATED save_graphic");
    var properties = graphic.attributes;
    
    //transform to geojson format
    var geojson_feature = {};
    geojson_feature.type = "Feature";
    geojson_feature.properties = properties;
    geojson_feature.geometry = {};
    
    if(graphic.geometry.type === "polyline") {
        geojson_feature.geometry.type = "LineString";
        geojson_feature.geometry.coordinates = graphic.geometry.paths[0];
    } else if(graphic.geometry.type === "point") {
        geojson_feature.geometry.type = "Point";
        geojson_feature.geometry.coordinates = [graphic.geometry.x,
                                                graphic.geometry.y];
    } else if(graphic.geometry.type === "polygon") {
        geojson_feature.geometry.type = "Polygon";
        geojson_feature.geometry.coordinates = graphic.geometry.rings;
    }
    
    if(graphic.id !== undefined && graphic.id !== null) {
        geojson_feature.id = graphic.id;
    }

    // add crs to the geometry
    geojson_feature.geometry.crs = {"type": "EPSG",
                                    "properties": {"code": graphic.geometry.spatialReference.wkid}};
     
    if(graphic.id !== undefined && graphic.id !== null) {
        update_feature(geojson_feature, callback_function);
    } else {
        create_feature(geojson_feature, callback_function);
    }
    
}


/*
This function removes a graphic.

It takes as parameters:
feature_id - id of the feature to be removed.
 
*/

function remove_graphic(feature_id, callback_function) {
    console.log("DEPRACATED remove_graphic");
    var feature = {
        'type' : 'Feature',
        'id': feature_id};
    delete_feature(feature, callback_function);
}

/*
Semaphore set with the layer as key

The problem is that there should only be one GET request
for each layer otherwise it adds the graphics twice.
*/
var LAYER_ADD_SEMAPHORES = {};

/*
The graphics queried from the server will be cached in the layer
but this helper variable tells if the layer graphics has already
been queried.
*/
var QUERIED_PARAM = {};

/*
This function gets graphics from the server

and adds them to the map_layer given

expects the layer to have a renderer of its own

It takes as parameters:
limiter_param - query string to limit the returned graphics
map_layer - the map layer where the graphics are added
infotemplate - an ESRI infotemplate object for the graphic

*/
function get_graphics(limiter_param, map_layer, infotemplate, callback_function) {
    console.log("DEPRACATED get_graphics");
    
    if(limiter_param === undefined ||
        limiter_param === null) {
        limiter_param = '';
    }

    //do not query twice with the same parameters
    if(QUERIED_PARAM[limiter_param]) {
        return;
    } else {
        QUERIED_PARAM[limiter_param] = true;
    }

    dojo.xhrGet({
        "url": api_full_url + '{% url api_feature %}' + limiter_param,
        "handleAs": "json",
        "sync": false,
        "headers": {"Content-Type":"application/json",
                    "X-CSRFToken": getCookie( CSRF_Cookie_Name ) },

        // The LOAD function will be called on a successful response.
        "load": function(response, ioArgs) {
                    var return_graphics = [];
                    var i = 0;

                    LAYER_ADD_SEMAPHORES[limiter_param] = true;

                    var spatialReference = new esri.SpatialReference({"wkid": response.crs.properties.code});
                    for(i = 0; i < response.features.length; i++) {
                        var geometry = response.features[i].geometry;
                        var properties = response.features[i].properties;
                        var id = response.features[i].id;
                        var graphic = new esri.Graphic({});

                        //graphicID and id should be the same
                        //properties.graphicID = id;
                        if(geometry.type === "Point") {
                            graphic.setGeometry(new esri.geometry.Point(geometry.coordinates).setSpatialReference(spatialReference));
                        } else if (geometry.type === "LineString") {
                            graphic.setGeometry(new esri.geometry.Polyline({"paths": [geometry.coordinates]}).setSpatialReference(spatialReference));
                        } else if(geometry.type === "Polygon") {
                            graphic.setGeometry(new esri.geometry.Polygon({"rings": geometry.coordinates}).setSpatialReference(spatialReference));
                        }
                        graphic.setAttributes(properties);
                        
                        graphic.id = id;
                        
                        if(infotemplate !== undefined) {
                            graphic.setInfoTemplate(infotemplate);
                        }
                        
                        if(map_layer !== undefined) {
                            map_layer.add(graphic);
                        }
                        return_graphics.push(graphic);
                        
                    }
                    
                    LAYER_ADD_SEMAPHORES[limiter_param] = false;
                    
                    return return_graphics;
                },

        // The ERROR function will be called in an error case.
        "error": function(response, ioArgs) {
            if (djConfig.debug) {
                console.error("HTTP status code: ", ioArgs.xhr.status);
            }
            return response;
        },
        "handle": function(response, ioArgs) {
            if(callback_function !== undefined) {
                callback_function({"response": response,
                                  "ioArgs": ioArgs});
            }
        }
    });
}
