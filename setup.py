from setuptools import setup
from setuptools import find_packages

setup(
    name='geojson_rest',
    version='5.2.1',
    author='Kristoffer Snabb',
    url='https://github.com/geonition/django_geojson_rest',
    packages=find_packages(),
    include_package_data=True,
    package_data = {
        "geojson_rest": [
            "templates/*.js",
            "templates/*.html"
        ],
    },
    install_requires=['django',
                      'psycopg2',
                      'geonition_utils'],
    dependency_links = [
        'https://github.com/geonition/django_geonition_utils/tarball/4.0.1#egg=geonition_utils-4.0.1'
        ],
    zip_safe=False
)
