from setuptools import setup, find_packages
from subprocess import Popen, PIPE


def call_git_describe(abbrev):
    try:
        p = Popen(['git', 'describe', '--abbrev=%d' % abbrev],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0].strip()
        line_str = line.decode('ascii')
        return line_str

    except subprocess.CalledProcessError as e:
        print(e.output)
        return None


setup(name='dashio',
      version=call_git_describe(7),
      # py_modules=['iotcontrol', 'iotconnection'],
      description='Dashio interface library',
      author='James Boulton',
      author_email='james.boulton@kotukublue.com',
      url="https://github.com/dashio-connect/python-dashio",
      # package_dir={'': 'dashio'},
      packages=find_packages(),
      license='MIT',
      classifiers=[
          "Programming Language :: Python :: 3",
          "Operating System :: OS Independent"
      ],
      install_requires=[
          'paho-mqtt'
      ]

      )
