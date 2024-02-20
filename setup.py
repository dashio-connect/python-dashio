from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dashio",
    version="3.4.6",
    description="DashIO interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="James Boulton",
    author_email="james@dashio.com",
    url="https://dashio.io",
    download_url="https://github.com/dashio-connect/python-dashio",
    packages=find_packages(),
    package_data={"dashio": ["py.typed"]},
    license="MIT",
    classifiers=["Programming Language :: Python :: 3.8", "Operating System :: OS Independent"],
    install_requires=["paho-mqtt>=2.0.0", "pyzmq", "python-dateutil", "zeroconf", "shortuuid", "pyserial", "astral", "pydantic"],
    python_requires='>3.7.0',
    scripts=['utilities/c64_encode', 'utilities/c64_decode'],
)
