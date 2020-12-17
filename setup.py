from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dashio",
    version="1.99.9",
    # py_modules=['iotcontrol', 'iotconnection'],
    description="Dashio interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="James Boulton",
    author_email="james.boulton@kotukublue.com",
    url="https://github.com/dashio-connect/python-dashio",
    # package_dir={'': 'dashio'},
    packages=find_packages(),
    license="MIT",
    classifiers=["Programming Language :: Python :: 3", "Operating System :: OS Independent"],
    install_requires=["paho-mqtt", "pyzmq", "python-dateutil", "zeroconf", "shortuuid"],
)

