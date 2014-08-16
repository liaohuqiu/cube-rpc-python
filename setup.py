from setuptools import setup, find_packages

setup(
    name = 'cubi',
    version = '0.0.7',
    keywords = ('cube', 'cubi', 'cube-rpc'),
    description = 'python implementation for Cube RPC protocol',
    license = 'MIT License',
    install_requires = ['bp', 'gevent'],

    scripts = ['cubi-simple-server', 'cubi-simple-server-test', 'cubi-another-server', 'cubi-another-server-test'],

    author = 'http://www.liaohuqiu.net',
    author_email = 'liaohuqiu@gmail.com',
    url = 'https://github.com/liaohuqiu/cube-rpc-python',

    packages = find_packages(),
    platforms = 'any',
)
