CREATE OR REPLACE VIEW PointFeature 
AS SELECT * FROM geojson_rest_feature WHERE GeometryType(geometry) = 'POINT';
CREATE OR REPLACE VIEW PointFeatureProperty 
AS SELECT * FROM geojson_rest_feature_properties 
WHERE feature_id 
IN (SELECT id FROM PointFeature);