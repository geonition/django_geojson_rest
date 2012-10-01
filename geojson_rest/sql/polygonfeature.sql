CREATE OR REPLACE VIEW PolygonFeature AS SELECT * FROM geojson_rest_feature WHERE GeometryType(geometry) = 'POLYGON';
CREATE OR REPLACE VIEW PolygonFeatureProperty 
AS SELECT * FROM geojson_rest_feature_properties 
WHERE feature_id 
IN (SELECT id FROM PolygonFeature);