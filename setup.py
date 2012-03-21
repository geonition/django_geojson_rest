from setuptools import setup
from setuptools import find_packages

setup(
    name='geojson_rest',
    version='3.0.x',
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
    zip_safe=False,
    install_requires=['django']
)
