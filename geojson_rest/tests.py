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
        self.user1 = User.objects.create_user('user1','', 'passwd')
        self.user2 = User.objects.create_user('user2','', 'passwd')
        self.user3 = User.objects.create_user('user3','', 'passwd')
        self.user4 = User.objects.create_user('user4','', 'passwd')
        
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
        self.assertContains(response,
                            '"id"',
                            count = 1,
                            status_code = 201)
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
        #get not existing property
        pass
        
