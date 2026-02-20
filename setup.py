from setuptools import setup, find_packages

setup(
    name="onstar_component",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "onstar==0.1.2",
        "voluptuous",
    ],
)
