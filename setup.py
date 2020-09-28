from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dashio",
<<<<<<< HEAD
    version="1.42.4",
=======
    version="1.42.5",
>>>>>>> d93d946e97130fe3036e97afcdce9cc440f57289
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
    install_requires=["paho-mqtt", "zmq", "python-dateutil"],
)
