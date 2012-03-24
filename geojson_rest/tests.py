from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import simplejson as json
from models import Feature

@override_settings(SPATIAL_REFERENCE_SYSTEM_ID = 4326)
class GeoRESTTest(TestCase):

    def setUp(self):
        self.client = Client()

        #setup a testuser
        self.user1 = User.objects.create_user('user1','', 'passwd')
        self.user2 = User.objects.create_user('user2','', 'passwd')
        self.user3 = User.objects.create_user('user3','', 'passwd')
        self.user4 = User.objects.create_user('user4','', 'passwd')
        
        self.base_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [20, 30]},
            'properties': {}
        }
        self.base_featurecollection = {
            'type': 'FeatureCollection',
            'features': []
        }
    
    def test_invalid_json(self):
        """
        Tests wether the json sent to the server
        is valid as geojson and other reserved variables.
        """
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #these requests should all respond with an error message
        response = self.client.post(reverse('feat'),
                                    '',
                                    content_type='application/json')
        
    def test_create_and_get(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #make a new feature to save
        new_feature = self.base_feature
        
        #create a private feature
        new_feature.update({'properties': {'first': True,
                                           'private': True}})
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type='application/json')
        
        #returned feature should include id
        self.assertContains(response,
                            '"id"',
                            count = 1,
                            status_code = 201)
        
     
        #create another not private feature
        new_feature.update({'properties': {'first': False,
                                           'private': False}})
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type='application/json')
        
        #response should include a uri to the created feature
        
        #query features for user should have 2 of them
        
        #logout
        self.client.logout()
        
        #login as another user
        self.client.login(username = 'user2', password = 'passwd')
        
        #create not private feature to group test
        
        #create not private feature to group test2
        
        #query own features in group test
        #query own features in test2
        
        #query all features should not include other users private feature
        
        #logout
        self.client.logout()
        
        #query all features should include all except private features
        
    def test_bbox_query(self):
        """
        This function tests the bbox
        query parameter
        
        The bbox is given as any polygon coordinates.
        """

        self.client.login(username='user1', password='passwd')

        geojson_feature = {"type": "Feature",
                            "geometry": {"type":"Point",
                                        "coordinates":[0, 200]},
                            "properties": {"hello": "hello"}}
        response = self.client.post(reverse('feat'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')

        geojson_feature = {"type": "Feature",
                            "geometry": {"type":"Point",
                                        "coordinates":[200, 0]},
                            "properties": {"hello": "hello"}}
        response = self.client.post(reverse('feat'),
                                    json.dumps(geojson_feature),
                                    content_type='application/json')

        #query the first one
        response = self.client.get(reverse('feat') + "?bbox=[[[-10,190],[10,190],[10,210],[-10,210],[-10,190]]]")

        res_dict = json.loads(response.content)
        self.assertEquals(len(res_dict['features']),
                          1,
                          "the boundingbox query should have returned only one feature")
        
    
    def test_history(self):
        #features to save

        self.client.login(username='user1', password='passwd')
        
        #save some values into the database
        geojson_feature = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[100, 200]},
                "properties": {"some_prop":"history_value",
                               "id": 1}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[200, 200]},
                "properties": {"some_prop": 40,
                               "id": 2}},
                {"type": "Feature",
                "geometry": {"type":"Point",
                            "coordinates":[300, 200]},
                "properties": {"some_prop": 40,
                               "id": 3}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[400, 200]},
                 "properties": {"some_prop": True,
                               "id": 4}},
                {"type": "Feature",
                 "geometry": {"type":"Point",
                            "coordinates":[500, 200]},
                 "properties": {"some_prop": 42,
                               "id": 5}}
                ]
        }


        before_create = datetime.datetime.now()

        time.sleep(1) #wait a second to get smart queries

        response = self.client.post(reverse('feat'),
                                json.dumps(geojson_feature),
                                content_type='application/json')

        response_dict = json.loads(response.content)

        #QUERY time__now=true and check that five features are returned
        response = self.client.get(reverse('feat') + \
                                   "?time__now=true")

        response_dict = json.loads(response.content)
        amount_of_features = len(response_dict['features'])

        self.assertTrue(amount_of_features == 5,
                        "Query with time__now after first post did not return 5 " + \
                        "geojson Features. It returned %i" % amount_of_features)

        #query with time__now and prop
        response = self.client.get(reverse('feat') + \
                                   "?time__now=true&some_prop=40")

        response_dict = json.loads(response.content)
        amount_of_features = len(response_dict['features'])
        if getattr(settings, "USE_MONGODB", False):
            self.assertTrue(amount_of_features == 2,
                            "Query with time__now and prop = 40 after first " + \
                            "post did not return 2 geojson Features. It returned %i" \
                            % amount_of_features)
        else:
            self.assertTrue(amount_of_features == 5,
                            "Query with time__now and prop = 40 after first " + \
                            "post did not return 5 geojson Features. It returned %i" \
                            % amount_of_features)


        #wait a little bit to get difference
        time.sleep(1)
        after_create = datetime.datetime.now()
        time.sleep(1)
        response_dict['features'][0]['properties']['good'] = 33
        updated_feature_id = response_dict['features'][0]['id']
        response = self.client.put(reverse('feat'),
                                json.dumps(response_dict['features'][0]),
                                content_type='application/json')

        #delete one and check that the next delete does not affect it
        time.sleep(1)
        after_update = datetime.datetime.now()

        response = self.client.get(reverse('feat') + "?time__now=true")
        response_dict = json.loads(response.content)

        ids = []
        for feat in response_dict['features']:
            ids.append(feat['id'])

        deleted_feature_id = ids[0]
        response = self.client.delete(reverse('feat') + "?ids=[%s]" % deleted_feature_id)

        time.sleep(1)
        after_first_delete = datetime.datetime.now()

        #wait a little bit more
        time.sleep(1)
        response = self.client.delete(reverse('feat') + "?ids=%s" % json.dumps(ids))


        #wait a little bit more
        time.sleep(1)
        after_delete = datetime.datetime.now()



        #start querying

        #before first post there should be nothing
        response = self.client.get(reverse('feat') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (before_create.year,
                                                            before_create.month,
                                                            before_create.day,
                                                            before_create.hour,
                                                            before_create.minute,
                                                            before_create.second))

        response_dict = json.loads(response.content)
        self.assertTrue(len(response_dict['features']) == 0,
                        "Query with time before first post did not return an empty FeatureCollection")

        #query after first post
        response = self.client.get(reverse('feat') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_create.year,
                                                            after_create.month,
                                                            after_create.day,
                                                            after_create.hour,
                                                            after_create.minute,
                                                            after_create.second))

        response_dict = json.loads(response.content)
        amount_of_features = len(response_dict['features'])

        for feat in response_dict['features']:
            if feat['id'] == updated_feature_id:
                self.assertEquals(feat['properties'].has_key('good'),
                                  False,
                                  "The feature retrieved does not seem to have correct properties" + \
                                  " querying time before an update")


        self.assertTrue(amount_of_features == 5,
                        "Query with time after first post did not return 5 " + \
                        "geojson Features. It returned %i" % amount_of_features)


        #query after update
        response = self.client.get(reverse('feat') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_update.year,
                                                            after_update.month,
                                                            after_update.day,
                                                            after_update.hour,
                                                            after_update.minute,
                                                            after_update.second))

        response_dict = json.loads(response.content)
        for feat in response_dict['features']:
            if feat['id'] == updated_feature_id:
                self.assertEquals(feat['properties'].has_key('good'),
                                  True,
                                  "The feature retrieved does not seem to have correct properties" + \
                                  " querying time before an update")
                self.assertEquals(feat['properties']['good'],
                                  33,
                                  "The feature updated does not seem to have correct properties" + \
                                  " querying time after an update")

        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 5,
                        "Query with time after update did not return 5 " + \
                        "geojson Features. It returned %i" % amount_of_features)


        #query after first delete
        response = self.client.get(reverse('feat') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_first_delete.year,
                                                            after_first_delete.month,
                                                            after_first_delete.day,
                                                            after_first_delete.hour,
                                                            after_first_delete.minute,
                                                            after_first_delete.second))


        response_dict = json.loads(response.content)


        #the deleted feature id should not be in the response
        for feature in response_dict['features']:
            self.assertNotEquals(feature['id'],
                                deleted_feature_id,
                                "Feature with id %i should have been deleted(expired) already" % deleted_feature_id)

        #query after deletion
        response = self.client.get(reverse('feat') + \
                                   "?time=%i-%i-%i-%i-%i-%i" % (after_delete.year,
                                                            after_delete.month,
                                                            after_delete.day,
                                                            after_delete.hour,
                                                            after_delete.minute,
                                                            after_delete.second))

        response_dict = json.loads(response.content)

        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 0,
                        "Query with time after delete did not return 0 " + \
                        "geojson Features. It returned %i" % amount_of_features)


        #query with time__now=true should return the server time now features
        response = self.client.get(reverse('feat') + "?time__now=true")

        response_dict = json.loads(response.content)

        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 0,
                        "Query with time__now=true did not return 0 " + \
                        "geojson Features. It returned %i" % amount_of_features)

        #query with time__now=false should return all
        response = self.client.get(reverse('feat') + \
                                   "?time__now=false")

        response_dict = json.loads(response.content)

        amount_of_features = len(response_dict['features'])
        self.assertTrue(amount_of_features == 6,
                        "Query with time__now=false did not return right amount of features  " + \
                        "geojson Features. It returned %i" % amount_of_features)