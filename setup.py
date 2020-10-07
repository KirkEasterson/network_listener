
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='mininet_listener',
    version='1.0.0',
    description='An event handler for Mininet that will generate PTF source code. ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/KirkEasterson/mininet_listener',
    author='Kirk Easterson',
    author_email='kirkeasterson@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='mininet, ptf, p4lang',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.5, <4',
    dependency_links=['https://github.com/p4lang/ptf/tarball/master'],
    project_urls={
        'Bug Reports': 'https://github.com/KirkEasterson/mininet_listener/issues',
        'Source': 'https://github.com/KirkEasterson/mininet_listener',
    },
)
