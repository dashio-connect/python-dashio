from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dashio",
    version="2.1.3",
    description="Dashio interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="James Boulton",
    author_email="james@dashio.com",
    url="https://github.com/dashio-connect/python-dashio",
    packages=find_packages(),
    license="MIT",
    classifiers=["Programming Language :: Python :: 3.6", "Operating System :: OS Independent"],
    install_requires=["paho-mqtt", "pyzmq", "python-dateutil", "zeroconf", "shortuuid"],
    python_requires='>3.6.0',
)
