from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
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

        #set up some features
        self.feat1 = Feature(
                        user = self.user1,
                        geometry = 'POINT(30 20)',
                        group = 'group1').save()
        self.feat2 = Feature(
                        user = self.user2,
                        geometry = 'POINT(20 30)',
                        group = 'group1').save()



    def test_get_queries(self):
        # get feature without logging in should work
        # returns all features for a specific user or group that
        # is not marked as private
        print reverse('geo')
        self.client.get(reverse('geo'))

        # get features after logging in that is marked private for the
        # logged in user

        #
