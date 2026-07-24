from io import open
from setuptools import setup

with open('README.md') as read_me:
    long_description = read_me.read()

setup(
    name='Glue',
    version='0.3.5',
    author='alepodj',
    url='https://github.com/alepodj/Glue',
    packages=['glue'],
    package_data={
        'glue': ['glue.js', 'py.typed'],
    },
    install_requires=[
        'bottle<1.0.0',
        'bottle-websocket<1.0.0',
        'gevent',
        'gevent-websocket<1.0.0',
        'pyparsing>=3.0.0,<4.0.0',
        'typing_extensions>=4.3.0',
        'importlib_resources>=1.3',
    ],
    extras_require={
        'jinja2': ['jinja2>=2.10'],
        'build': ['pyinstaller'],
    },
    python_requires='>=3.7',
    description='For little HTML GUI applications, with easy Python/JS interop',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['gui', 'html', 'javascript', 'desktop', 'chrome', 'edge'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: MIT License',
    ],
)
