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
    
    def test_create(self):
        #login the user
        self.client.login(username = 'user1',
                          password = 'passwd')
        
        #make a new feature to save
        new_feature = self.base_feature
        new_feature.update({'properties': 'first'})
        
        #create the feature
        response = self.client.post(reverse('feat'),
                                    json.dumps(new_feature),
                                    content_type='application/json')
        
        #feature should include id
        self.assertContains(response,
                            '"id"',
                            count = 1,
                            status_code = 201)
        
        # the response should include a Location header
        # with the created resource URI
        