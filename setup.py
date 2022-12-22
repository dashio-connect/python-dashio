from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dashio",
    version="3.2.1",
    description="DashIO interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="James Boulton",
    author_email="james@dashio.com",
    url="https://dashio.io",
    download_url="https://github.com/dashio-connect/python-dashio",
    packages=find_packages(),
    license="MIT",
    classifiers=["Programming Language :: Python :: 3.6", "Operating System :: OS Independent"],
    install_requires=["paho-mqtt", "pyzmq", "python-dateutil", "zeroconf", "shortuuid", "pyserial", "astral"],
    python_requires='>3.6.0',
)
