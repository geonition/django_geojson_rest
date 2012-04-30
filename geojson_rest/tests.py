from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import simplejson as json
from models import Feature
from time import sleep

@override_settings(SPATIAL_REFERENCE_SYSTEM_ID = 4326)
class GeoRESTTest(TestCase):

    def setUp(self):
        self.client = Client()

        #setup a testuser
        self.user1 = User.objects.create_user('user1', '', 'passwd')
        self.user2 = User.objects.create_user('user2', '', 'passwd')
        self.user3 = User.objects.create_user('user3', '', 'passwd')
        self.user4 = User.objects.create_user('user4', '', 'passwd')
        
        self.base_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [20, 30]},
            'properties': {},
            'private': True
        }
        self.base_featurecollection = {
            'type': 'FeatureCollection',
            'features': []
        }
        
    def test_create_and_get_feature(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #make a new feature to save
        new_feature = self.base_feature
        
        #create a private feature
        new_feature.update({
            'properties': {'first': True}
            })
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        
        response_json = json.loads(response.content)
        #returned feature should include id
        response_dict = json.loads(response.content)
        self.assertTrue(response_dict.has_key('id'),
                        'The response feature did not have a key')
        self.assertEquals(response.status_code,
                          201,
                          'The response was not a 201 created')
        self.assertTrue(response_json['private'],
                        'The feature returned did not include a private key')
        
     
        #create another not private feature
        new_feature.update({'properties': {'first': False}})
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        
        #response should include a uri to the created feature
        self.assertTrue(response.has_header('Location'),
                        'The response did not inlcude a "Location" header')
        
        #query features for user should have 2 of them
        response = self.client.get(reverse('feat'))
        
        #logout
        self.client.logout()
        
        #login as another user
        self.client.login(username = 'user2', password = 'passwd')
        
        #create not private feature to group test
        new_feature.update({'private': False})
        response = self.client.post(reverse('feat') + '/@me/test',
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_json = json.loads(response.content)
        self.assertFalse(response_json['private'],
                         'The response of creating was not private false')
        
        #create not private feature to group test2
        new_feature.update({'private': False})
        response = self.client.post(reverse('feat') + '/@me/test2',
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_json = json.loads(response.content)
        self.assertEquals(response_json['group'],
                          'test2',
                          'The response feature did not belong to group "test2"')
        
        #query own features in group test
        response = self.client.get(reverse('feat') + '/@me/test')
        response_json = json.loads(response.content)
        self.assertEquals(len(response_json['features']),
                          1,
                          'Querying features in group test did not return 1 feature')
        
        #query own features in test2
        response = self.client.get(reverse('feat') + '/@me/test2')
        response_json = json.loads(response.content)
        self.assertEquals(len(response_json['features']),
                          1,
                          'Querying features in group test2 did not return 1 feature')
        
        #query all features should not include other users private features
        response = self.client.get(reverse('feat') + '/@all/@all')
        response_json = json.loads(response.content)
        #because all user1 features are private this shuold return 2
        self.assertEquals(len(response_json['features']),
                              2,
                              'Querying all features returned not private features')
        
        #logout
        self.client.logout()
        
        #query all features should include all except private features
        response = self.client.get(reverse('feat') + '/@all/@all')
        response_json = json.loads(response.content)
        for feat in response_json['features']:
            self.assertFalse(feat['private'],
                             'Querying all returned private features')
            
    def test_update_and_get_feature(self):
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #make a new feature to save
        new_feature = self.base_feature
        
        #create a feature
        new_feature.update({
            'properties': {'first': True}
            })
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_json = json.loads(response.content)
        self.assertTrue(response_json['properties']['first'])
        
        #update the feature
        new_feature.update({
            'properties': {'first': False}
            })
        feature_id = response_json['id']
        
        response = self.client.put(reverse('feat') + '/@me/@self/' + str(feature_id),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_json = json.loads(response.content)
        self.assertFalse(response_json['properties']['first'])
        feature_id = response_json['id']

        #query the feature and check updated value
        response = self.client.get(reverse('feat') + '/@all/@all/' + str(feature_id))
        response_json = json.loads(response.content)
        
        self.assertFalse(response_json['features'][0]['properties']['first'])
        
    def test_create_and_delete_feature(self):
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #create a feature
        new_feature = self.base_feature
        
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_json = json.loads(response.content)
        feature_id = response_json['id']
        
        #query the feature
        response = self.client.get(reverse('feat') + '/@me/@self/' + str(feature_id))
        response_json = json.loads(response.content)
        self.assertEquals(len(response_json['features']),
                          1,
                          'A feature was not created')
        
        #delete feature
        response = self.client.delete(reverse('feat') + '/@me/@self/' + str(feature_id))
        
        #query feature
        response = self.client.get(reverse('feat') + '/@me/@self/' + str(feature_id))
        response_json = json.loads(response.content)
        
        self.assertEquals(len(response_json['features']),
                          0,
                          'the feature was not deleted')
        
    def test_create_and_get_property(self):
        #login to the service
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #get not existing property
        response = self.client.get(reverse('prop') + '/@me/test_group/3/500')
        
        self.assertEquals(response.status_code,
                          404,
                          "Querying a non existing feature did not return 404")
       
        #create a feature with property to group @self and user @me
        new_feature = self.base_feature
        new_feature.update({'properties': {'first': False}})
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')        
        self.assertEquals(response.status_code,
                          201,
                          "Creating a feature did not return a 201 created")
        feature_id = json.loads(response.content)['id']
        property_id = json.loads(response.content)['properties']['id']
        
        #query property saved with feature
        response = self.client.get('%s/@me/@self/%i/%i' % (reverse('prop'),
                                                           feature_id,
                                                           property_id))
        self.assertEquals(response.status_code,
                          200,
                          "Querying a property did not return status code 200")
        self.assertEquals(json.loads(response.content)['group'],
                          '@self',
                          'The property did not belong to @self group')
                          
        
        #create property without feature to group 'test_group'
        response = self.client.post(reverse('prop') + '/@me/test_group/@null',
                                    json.dumps({'key': 'first saved'}),
                                    content_type = 'application/json')   
        self.assertEquals(response.status_code,
                          201,
                          "Creating a property did not return a 201 created")
        
        property_id = json.loads(response.content)['id']
        
        #query property saved without feature
        response = self.client.get('%s/@me/test_group/@null/%i' % (reverse('prop'),
                                                                   property_id))
        self.assertEquals(response.status_code,
                          200,
                          "Querying a property did not return status code 200")
        self.assertEquals(json.loads(response.content)['group'],
                          'test_group',
                          'The property did not belong to test_group group')
        
        #query all user1 properties
        response = self.client.get('%s/user1' % reverse('prop'))
        self.assertTrue(json.loads(response.content).has_key('totalResults'),
                        'The returned collection did not have key totalResults')
        self.assertTrue(json.loads(response.content).has_key('entry'),
                        'The returned collection did not have key entry')
        
        #update property
        update_to_values = {'hello': 'world'}
        response = self.client.put('%s/@me/test_group/@null/%i' % (reverse('prop'),
                                                                   property_id),
                                   json.dumps(update_to_values),
                                   content_type = "application/json"
                                   )
        
        self.assertTrue(json.loads(response.content).has_key('hello'),
                        'A key was not found in updated property')
        
        #delete property
        response = self.client.delete('%s/@me/test_group/@null/%i' % (reverse('prop'),
                                                                      property_id))
        
        self.assertEquals(response.status_code,
                          200,
                          'Deleting a feature did not return 200 OK')
        
        #get property and check that it does not exist
        response = self.client.get('%s/@me/test_group/@null/%i' % (reverse('prop'),
                                                                   property_id))
        
        self.assertEquals(response.status_code,
                          404,
                          'Querying a deleted property did not return not found')
        
