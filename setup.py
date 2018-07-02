from setuptools import setup, find_packages


setup(
    name='bnl_provenance',
    version='0.0.0',
    packages=find_packages(),
    description='materials schema',
    zip_safe=False,
    package_data={'sciprovanance': ['schemas/*']},
    include_package_data=True,
)
