from setuptools import setup

from rainbowalga import version

setup(name='rainbowalga',
      version=version,
      url='http://github.com/tamasgal/rainbowalga/',
      description='A 3D event display for KM3NeT',
      author='Tamas Gal',
      author_email='tgal@km3net.de',
      packages=['rainbowalga'],
      include_package_data=True,
      platforms='any',
      install_requires=[
          'numpy',
          'docopt',
          'km3pipe>=2.5.2',
          'Pillow>=3.1.0',
          'PyOpenGL',
          'freetype-py',
          'matplotlib',
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
