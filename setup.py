#!/usr/bin/env python
"""
Setup script for ADB Manager Pro
Supports building standalone executables and distributions
"""

import sys
from setuptools import setup

setup(
    name='ADB Manager Pro',
    version='1.0.0',
    description='User-friendly software for ADB and Fastboot tools with device detection',
    author='ADB Manager Dev',
    author_email='',
    url='https://github.com/yourusername/adb-manager-pro',
    license='MIT',
    py_modules=['main', 'config', 'tool_manager', 'device_manager', 'database', 'ui'],
    install_requires=[
        'PyQt5==5.15.9',
        'PyQt5-sip==12.13.0',
        'requests==2.31.0',
        'psutil==5.9.6',
        'PyInstaller==6.1.0',
    ],
    entry_points={
        'console_scripts': [
            'adb-manager=main:main',
        ],
        'gui_scripts': [
            'adb-manager-gui=ui:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Hardware',
        'Topic :: Utilities',
    ],
    keywords='adb fastboot android device management',
    python_requires='>=3.7',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
