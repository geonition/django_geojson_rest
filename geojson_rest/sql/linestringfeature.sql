CREATE OR REPLACE VIEW LinestringFeature 
AS 
SELECT * FROM geojson_rest_feature 
WHERE GeometryType(geometry) = 'LINESTRING';
CREATE OR REPLACE VIEW LinestringFeatureProperty 
AS SELECT * FROM geojson_rest_feature_properties 
WHERE feature_id 
IN (SELECT id FROM LinestringFeature);