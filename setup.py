from setuptools import setup

import rainbowalga

setup(name='rainbowalga',
      version=rainbowalga.version,
      url='http://github.com/tamasgal/rainbowalga/',
      description='A 3D event display for KM3NeT',
      author='Tamas Gal',
      author_email='tgal@km3net.de',
      packages=['rainbowalga']
      include_package_data=True,
      platforms='any',
      install_requires=[
          'numpy',
          'docopt',
          'km3pipe',
          'Pillow',
          'PyOpenGL',
          'freetype-py',
      ],
      entry_points={
          'console_scripts': [
              'rainbowalga=rainbowalga.__main__:main',
          ],
      },
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
      ],
)

__author__ = 'Tamas Gal'