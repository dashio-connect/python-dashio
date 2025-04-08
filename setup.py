from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="dashio",
    version="3.5.3",
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
    install_requires=["paho-mqtt>=2.0.0", "pyzmq", "python-dateutil", "zeroconf", "shortuuid", "pyserial"],
    python_requires='>=3.8.0',
    scripts=['utilities/c64_encode', 'utilities/c64_decode', 'utilities/dashio_data_exporter'],
)
