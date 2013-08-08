#!/usr/bin/python
# -*- coding: utf-8 -*-

from actions import get_selectors
from models import Feature
from actions import download_csv
from admin import FeatureAdmin
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import simplejson as json
from time import sleep
from django.utils.unittest import skip
import csv
import copy

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

    # helper functions to return a new feature and new feature_collection
    def create_feature(self, prop_dict=None):
        new_feat = copy.deepcopy(self.base_feature)
        if prop_dict != None:
            new_feat['properties'] = prop_dict
        return new_feat

    def create_feature_collection(self):
        return copy.deepcopy(self.base_featurecollection)

    def test_unauthorized_feature_get(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new public feature to save
        new_feature = self.create_feature()
        new_feature.update({'private': False})
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']
        self.client.logout()

        #try to get a feature
        response = self.client.get(reverse('feat') + "/@me/@self/" + str(id))
        self.assertEquals(response.status_code,
                          401,
                          'The response was not a 401, not signed in user could get a public feature')

        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new private feature to save
        new_feature = self.create_feature()
        new_feature['geometry']['coordinates'] = [10,10]
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']

        self.client.logout()

        self.client.login(username = 'user2',
                          password = 'passwd')

        response = self.client.get(reverse('feat') + '/user2/@self/' + str(id))
#        self.assertEquals(response.status_code,
#                          404,
#                          'The response was not a 404 as in documentation')
        response_json = json.loads(response.content)
        self.assertEquals(len(response_json['features']),
                          0,
                          'Querying another user private feature returned feature')

        #Query all user1 public features
        response = self.client.get(reverse('feat') + '/user1')
        self.assertEquals(response.status_code,
                          200,
                          'The response was not a 200')

        response_json = json.loads(response.content)
        self.assertNotEqual(len(response_json['features']),
                          0,
                          'Querying all public features did not return any')

        self.assertNotEqual(len(response_json['features']),
                          2,
                          'Querying all public features returned also private features')
        #make a new private feature to save
        new_feature = self.create_feature()
        #save feature for user user2
        response = self.client.post(reverse('feat') + '/user2',
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']

        #try to get that feature
        response = self.client.get(reverse('feat') + '/user2/@self/' + str(id))
        self.assertEquals(response.status_code,
                          200,
                          'The response was not a 200')

        response_json = json.loads(response.content)
        self.assertEquals(len(response_json['features']),
                          1,
                          'Querying user user2 features did not return any')

    def test_delete_other_users_feature(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new public feature to save
        new_feature = self.create_feature()
        new_feature.update({'private': False})
        new_feature.update({'properties':{'deleteTest': True}})
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']
        self.client.logout()

        #try to get a feature
        response = self.client.delete(reverse('feat') + '/@me/@self/' + str(id))
        self.assertEqual(response.status_code,
                          403,
                          'The response was not a 403, other users public feature might be deleted by not signed in user')


        #login the user1 back to check if feature was really deleted
        self.client.login(username = 'user1',
                          password = 'passwd')

        response = self.client.get(reverse('feat'))
        response_json = json.loads(response.content)
        self.assertEqual(len(response_json['features']),
                          1,
                          'Trying to delete other users feature did actually delete the feature')

    def test_unauthorized_feature_post(self):
        #make a new feature to save
        new_feature = self.create_feature()


        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')


        response = self.client.post(reverse('feat') + "/user2",
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        self.assertEqual(response.status_code,
                          403,
                          'response was not 403 for creating a feature to another user. response was %s: %s' %
                          (str(response.status_code), response.content))

    def test_unauthorized_feature_put(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        new_feature = self.create_feature()
        new_feature.update({
            'properties': {'first': False,
                           'second': "test string"}
            })
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        feature_id = response_dict['id']

        new_feature.update({
            'properties': {'first': True,
                           'third': 657677}
            })

        #test with no session
        #This crashes by design decision
#        self.client.logout()
#        response = self.client.put(reverse('feat') + '/@me/@self/' + str(feature_id),
#                                    json.dumps(new_feature),
#                                    content_type = 'application/json')
#
#        self.assertEqual(response.status_code,
#                          403,
#                          'The response was not a 403 for not signed in user')

        self.client.logout()
        #login another user
        self.client.login(username = 'user2',
                          password = 'passwd')


        response = self.client.put(reverse('feat') + '/user1/@self/' + str(feature_id),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        self.assertEqual(response.status_code,
                          403,
                          'The response was not a 403 for updating another user feature. response was %s: %s' %
                          (str(response.status_code), response.content))

    @skip("This documented feature is not in use and not working, see issue #30.")
    def test_add_property_to_another_users_feature(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        new_feature = self.create_feature()
        new_feature.update({
            'properties': {'first': False,
                           'second': "test string"}
            })
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        feature_id = response_dict['id']

        new_feature.update({
            'properties': {'first': True,
                           'third': 657677}
            })

        #test with no session
        #This crashes by design decision
#        self.client.logout()
#        response = self.client.put(reverse('feat') + '/@me/@self/' + str(feature_id),
#                                    json.dumps(new_feature),
#                                    content_type = 'application/json')
#
#        self.assertEqual(response.status_code,
#                          403,
#                          'The response was not a 403 for not signed in user')

        self.client.logout()
        #login another user
        self.client.login(username = 'user2',
                          password = 'passwd')



        response = self.client.put(reverse('feat') + '/@me/@self/' + str(feature_id),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        self.assertEqual(response.status_code,
                          200,
                          'The response was not a 200 for updating another user feature with new properties')

        #get the feature
        self.client.logout()
        #login user who owns the feature
        self.client.login(username = 'user1',
                          password = 'passwd')
        response = self.client.get(reverse('feat') + '/@me/@self/' + str(feature_id))

        response_dict = json.loads(response.content)
        feature_properties = response_dict['features'][0]['properties']
        self.assertEqual(len(feature_properties),
                         2,
                         'Only one set of properties returned.')

    def test_unauthorized_property_get(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new property to save
        new_property = {'first': 'first',
                        'second': 5}
        response = self.client.post(reverse('prop'),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']
        self.client.logout()

        #try to get a property
#        response = self.client.get(reverse('prop') + "/user1/@self/@null/" + str(id))
#        self.assertEquals(response.status_code,
#                          400,
#                          'The response was not a 400, not signed in user could get a property')

        self.client.login(username = 'user2',
                          password = 'passwd')

        response = self.client.get(reverse('prop') + '/user1/@self/@null/' + str(id))
        self.assertEquals(response.status_code,
                          200,
                          'The response was not a 200, property was not a public one')
        response_json = json.loads(response.content)

        self.client.logout()
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new property to save
        new_property = {'first': 'second',
                        'second': False}
        response = self.client.post(reverse('prop'),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        id = response_dict['id']

        self.client.logout()
        #login the user
        self.client.login(username = 'user2',
                          password = 'passwd')

        #Query all user1 properties
        response = self.client.get(reverse('prop') + '/user1')

        self.assertEquals(response.status_code,
                          200,
                          'The response was not a 200')

        response_json = json.loads(response.content)
        self.assertNotEqual(len(response_json['entry']),
                          0,
                          'Querying all properties did not return any')

        self.assertEqual(len(response_json['entry']),
                          2,
                          'Querying all properies returned only one.')

        #Query all properties as @me
        response = self.client.get(reverse('prop'))
        self.assertEquals(response.status_code,
                          404,
                          'The response was not a 404')

        response_json = json.loads(response.content)
        self.assertEqual(response_json['msg'],
                          'The property you queried was not found',
                          'Returned message was not correct')


    def test_unauthorized_property_post(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        new_property = {'first': 'first',
                        'second': 5}
        response = self.client.post(reverse('prop') + "/user2",
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)

        self.assertEqual(response.status_code,
                          403,
                          'response was not 403 for creating a property to another user. response was %s: %s' %
                          (str(response.status_code), response.content))

    def test_unauthorized_property_put(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        new_property = {'first': 'first',
                        'second': 5}
        response = self.client.post(reverse('prop'),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        property_id = response_dict['id']

        new_property.update({'first': True,
                           'third': 657677})


        self.client.logout()
        #login another user
        self.client.login(username = 'user2',
                          password = 'passwd')


        response = self.client.put(reverse('prop') + '/user1/@self/@null/' + str(property_id),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        self.assertEqual(response.status_code,
                          403,
                          'The response was not a 403 for updating another user property. response was %s: %s' %
                          (str(response.status_code), response.content))

    def test_delete_other_users_property(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        new_property = {'first': 'first',
                        'second': 5}
        response = self.client.post(reverse('prop'),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        property_id = response_dict['id']
        self.client.logout()

        #try to delete a feature
        response = self.client.delete(reverse('prop') + '/@me/@self/@null/' + str(property_id))
        self.assertEqual(response.status_code,
                          403,
                          'The response was not a 403, other users public feature might be deleted by not signed in user')


        #login the user1 back to check if property was really deleted
        self.client.login(username = 'user1',
                          password = 'passwd')

        response = self.client.get(reverse('prop'))
        response_json = json.loads(response.content)
        self.assertTrue(response_json.has_key('group'),
                          'Trying to delete other users property did actually delete the feature')

#     @skip("When property is connected to feature, django tries to delete from database view\
#            because of the m2m field. This gives a database error")
    def test_add_and_delete_property_connected_to_feature(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #make a new feature to save
        new_feature = self.create_feature()
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        feature_id = response_dict['id']

        new_property = {'first': 'first',
                        'second': 5}
        response = self.client.post(reverse('prop') + '/@me/@self/' + str(feature_id),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)
        property_id = response_dict['id']

        # get the feature
        response = self.client.get(reverse('feat') + "/@me/@self/" + str(feature_id))
        response_dict = json.loads(response.content)
        prop = response_dict['features'][0]['properties']
        self.assertEqual(prop['first'], 'first', 'property did not get added to the feature')

        #update the property
        new_property.update({'first': 'second',
                        'second': False})

        response = self.client.put(reverse('prop') + '/@me/@self/' + str(feature_id) + '/' + str(property_id),
                                    json.dumps(new_property),
                                    content_type = 'application/json')

        response_dict = json.loads(response.content)

        # get the feature
        response = self.client.get(reverse('feat') + "/@me/@self/" + str(feature_id))
        response_dict = json.loads(response.content)
        prop = response_dict['features'][0]['properties']
        self.assertEqual(prop['first'], 'second', 'property did not get updated')

        # delete the property without feature_id
        response = self.client.delete(reverse('prop') + '/@me/@self/@null/' + str(property_id))
        self.assertEqual(response.status_code,
                          200,
                          'The response was not a 200. Delete without feature id was not succesfull')
        # get the feature
        response = self.client.get(reverse('feat') + "/@me/@self/" + str(feature_id))
        response_dict = json.loads(response.content)
        prop = response_dict['features'][0]['properties']
        self.assertFalse('first' in prop, 'property did not get deleted')


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
        new_feature.update({'private': True})
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

        self.client.logout()
        self.client.login(username = 'user1', password = 'passwd')

        #query all features should include all except private features
        response = self.client.get(reverse('feat') + '/@others/@all')
        response_json = json.loads(response.content)
        for feat in response_json['features']:
            self.assertFalse(feat['private'],
                             'Querying all returned private features')

        self.client.logout()

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
                          404,
                          "Querying a property did not return status code 404, returned: %s" % response.status_code)
#         self.assertEquals(json.loads(response.content)['group'],
#                           '@self',
#                           'The property did not belong to @self group')


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
                          "Querying a property did not return status code 200, returned: %s" % response.status_code)
        self.assertEquals(json.loads(response.content)['group'],
                          'test_group',
                          'The property did not belong to test_group group')

        #create another property to test multiple properties
        response = self.client.post(reverse('prop') + '/@me/test_group/@null',
                                    json.dumps({'another': 'first saved'}),
                                    content_type = 'application/json')
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


    def test_json_to_csv(self):
        tlist = [{'hello': 'world',
                  'list': ['a','b'],
                    'dict': {'hello': 'world',
                             'goodbye': 'world'}}]
        selector_list = get_selectors(tlist)
        self.assertEquals(selector_list,
                          ['dict.hello',
                           'dict.goodbye',
                           'list',
                           'hello'],
                          "The selector list was not what it should have been")

    def test_download_csv_with_nested_objects(self):
        feat2 = self.create_feature({'first': "test2"})
        feat3 = self.create_feature({'first': "test3", 'second': 2, 'third': {}})
        feat4 = self.create_feature({'first': "test4", 'third': {'test4': 'This will break the code'}})

        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #Post features to the database
        response = self.client.post(reverse('feat'),
                            json.dumps(feat4),
                            content_type = 'application/json')
        response_dict = json.loads(response.content)
        feat1_create_time = response_dict['time']['create_time']
        feat1_id = response_dict['id']
        feat1_prop_create_time = response_dict['properties']['time']['create_time']
        feat1_prop_id = response_dict['properties']['id']

        response = self.client.post(reverse('feat'),
                            json.dumps(feat3),
                            content_type = 'application/json')
        response_dict = json.loads(response.content)
        feat2_create_time = response_dict['time']['create_time']
        feat2_id = response_dict['id']
        feat2_prop_create_time = response_dict['properties']['time']['create_time']
        feat2_prop_id = response_dict['properties']['id']

        response = self.client.post(reverse('feat'),
                            json.dumps(feat2),
                            content_type = 'application/json')
        response_dict = json.loads(response.content)
        feat3_create_time = response_dict['time']['create_time']
        feat3_id = response_dict['id']
        feat3_prop_create_time = response_dict['properties']['time']['create_time']
        feat3_prop_id = response_dict['properties']['id']


        f_admin= FeatureAdmin(Feature,1)
        request = ""
        features = Feature.objects.all().order_by('pk')
        csv_response = download_csv(f_admin, request, features)


        csv_lines= []

        csv_lines.append(['group',
                          'user',
                          'time.expire_time',
                          'time.create_time',
                          'wkt',
                          'type',
                          'id',
                          'private',
                          'properties.group',
                          'properties.user',
                          'properties.third.test4',
                          'properties.time.expire_time',
                          'properties.time.create_time',
                          'properties.id',
                          'properties.first',
                          'properties.second'])

        csv_lines.append(['@self',
                          'user1',
                          '',
                          feat1_create_time,
                          'POINT (20.0000000000000000 30.0000000000000000)',
                          'Feature',
                          str(feat1_id),
                          'True',
                          '@self',
                          'user1',
                          'This will break the code',
                          '',
                          feat1_prop_create_time,
                          str(feat1_prop_id),
                          'test4',
                          ''])

        csv_lines.append(['@self',
                          'user1',
                          '',
                          feat2_create_time,
                          'POINT (20.0000000000000000 30.0000000000000000)',
                          'Feature',
                          str(feat2_id),
                          'True',
                          '@self',
                          'user1',
                          '',
                          '',
                          feat2_prop_create_time,
                          str(feat2_prop_id),
                          'test3',
                          '2'])
        csv_lines.append(['@self',
                          'user1',
                          '',
                          feat3_create_time,
                          'POINT (20.0000000000000000 30.0000000000000000)',
                          'Feature',
                          str(feat3_id),
                          'True',
                          '@self',
                          'user1',
                          '',
                          '',
                          feat3_prop_create_time,
                          str(feat3_prop_id),
                          'test2',
                          ''])
        csvr = csv.reader(csv_response)
        for index,line in enumerate(csvr):
            #First line is empty
            if index > 0:
                #We need to skip time
                self.assertEqual(csv_lines[index-1], line, 'csv line:%s is not correct\n %s != %s' % (index, csv_lines[index-1], line) )


    def test_download_csv_with_utf_8(self):
        feat1 = self.create_feature({u'first': u'äÄöÖåÅ€'})
        feat2 = self.create_feature({'secondä': u'Test'})

        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')

        #Post features to the database
        response = self.client.post(reverse('feat'),
                            json.dumps(feat1),
                            content_type = 'application/json')
        response_dict = json.loads(response.content)
        #print response_dict
        feat1_create_time = response_dict['time']['create_time']
        feat1_id = response_dict['id']
        feat1_prop_create_time = response_dict['properties']['time']['create_time']
        feat1_prop_id = response_dict['properties']['id']

        #Post features to the database
        response = self.client.post(reverse('feat'),
                            json.dumps(feat2),
                            content_type = 'application/json')
        response_dict = json.loads(response.content)
        #print response_dict
        feat2_create_time = response_dict['time']['create_time']
        feat2_id = response_dict['id']
        feat2_prop_create_time = response_dict['properties']['time']['create_time']
        feat2_prop_id = response_dict['properties']['id']

        f_admin= FeatureAdmin(Feature,1)
        request = ""
        features = Feature.objects.all().order_by('pk')
        csv_response = download_csv(f_admin, request, features)


        csv_lines= []

        csv_lines.append(['group',
                          'user',
                          'time.expire_time',
                          'time.create_time',
                          'wkt',
                          'type',
                          'id',
                          'private',
                          'properties.id',
                          'properties.first',
                          'properties.group',
                          'properties.user',
                          'properties.time.expire_time',
                          'properties.time.create_time',
                          'properties.secondä'])

        csv_lines.append(['@self',
                          'user1',
                          '',
                          feat1_create_time,
                          'POINT (20.0000000000000000 30.0000000000000000)',
                          'Feature',
                          str(feat1_id),
                          'True',
                          str(feat1_prop_id),
                          'äÄöÖåÅ€',
                          '@self',
                          'user1',
                          '',
                          feat1_prop_create_time,
                          '',
                          ])

        csv_lines.append(['@self',
                          'user1',
                          '',
                          feat2_create_time,
                          'POINT (20.0000000000000000 30.0000000000000000)',
                          'Feature',
                          str(feat2_id),
                          'True',
                          str(feat2_prop_id),
                          '',
                          '@self',
                          'user1',
                          '',
                          feat2_prop_create_time,
                          'Test',
                          ])

        csvr = csv.reader(csv_response)
        for index,line in enumerate(csvr):
            #First line is empty
            if index > 0:
                #We need to skip time
                self.assertEqual(csv_lines[index-1], line, 'csv line:%s is not correct\n %s != %s' % (index, csv_lines[index-1], line) )


class GeoRESTAdminTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user('user1', '', 'passwd')

        #setup a admin
        self.admin_user = User.objects.create_user('admin', '', 'passwd')
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()

        self.base_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [20, 30]},
            'properties': {},
            'private': True
        }

    def create_feature(self, prop_dict=None, geom_type='Point'):
        new_feat = copy.deepcopy(self.base_feature)
        linestring_coords = [
          [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
          ]
        polygon_coords = [
           [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
             [100.0, 1.0], [100.0, 0.0] ]
           ]
        if prop_dict != None:
            new_feat['properties'] = prop_dict

        if geom_type != 'Point':
            new_feat['geometry']['type'] = geom_type
            if geom_type == 'LineString':
                new_feat['geometry']['coordinates'] = linestring_coords
            else:
                new_feat['geometry']['coordinates'] = polygon_coords


        return new_feat



    def test_delete_feature(self):

        new_feature = self.create_feature()

        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')


        #save the feature
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_dict = json.loads(response.content)
        feat_id = response_dict['id']

        self.client.logout()

        self.client.login(username = 'admin', password = 'passwd')
        postdata = {'post' : 'yes'}
        response = self.client.post(reverse('admin:geojson_rest_feature_delete', args=(feat_id,)),
                                    postdata)
        self.assertEqual(response.status_code,
                          302,
                          "Deleting a feature did not return status code 302")

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code,
                          200,
                          "Deleting a feature redirect did not work")

        response = self.client.get(reverse('feat'))
        response_json = json.loads(response.content)

        self.assertEquals(len(response_json['features']),
                          0,
                          'the feature was not deleted')


    def test_delete_property_not_connected_to_feature(self):
        #new_feature = self.create_feature(prop_dict={'first': False}, geom_type='Polygon')

        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')


        #create property without feature
        response = self.client.post(reverse('prop') + '/@me/@self/@null',
                                    json.dumps({'key': 'first saved'}),
                                    content_type = 'application/json')

        property_id = json.loads(response.content)['id']

        self.client.logout()

        self.client.login(username = 'admin', password = 'passwd')

        postdata = {'post' : 'yes'}
        #Test delete property not connected to feature
        response = self.client.post(reverse('admin:geojson_rest_property_delete', args=(property_id,)),
                                    postdata)
        self.assertEqual(response.status_code,
                          302,
                          "Deleting a property did not return status code 302")

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code,
                          200,
                          "Deleting a property redirect did not work")

        response = self.client.get('%s/@me/@self/@null/%i' % (reverse('prop'),
                                                                   property_id))

        self.assertEquals(response.status_code,
                          404,
                          'Querying a deleted property did not return not found')

#     @skip("When property is connected to feature, django tries to delete from database view\
#            because of the m2m field. This gives a database error")
    def test_delete_property_connected_to_feature(self):
        new_feature = self.create_feature(prop_dict={'first': False}, geom_type='Polygon')

        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')


        #save the feature
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type = 'application/json')
        response_dict = json.loads(response.content)
        feat_id = response_dict['id']
        property_connected_to_feature_id = response_dict['properties']['id']

        self.client.logout()

        self.client.login(username = 'admin', password = 'passwd')

        postdata = {'post' : 'yes'}

        #Test delete property connected to feature
        response = self.client.post(reverse('admin:geojson_rest_property_delete', args=(property_connected_to_feature_id,)),
                                    postdata)
        self.assertEqual(response.status_code,
                          302,
                          "Deleting a property did not return status code 302")

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code,
                          200,
                          "Deleting a property redirect did not work")

        response = self.client.get('%s/@me/@self/@null/%i' % (reverse('prop'),
                                                                   property_connected_to_feature_id))

        self.assertEquals(response.status_code,
                          404,
                          'Querying a deleted property did not return not found')

