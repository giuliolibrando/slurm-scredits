from setuptools import setup, find_packages

setup(
    name='scredits',
    version='1.1.2', 
    packages=find_packages(),
    install_requires=[
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'scredits=scredits.cli:main',
        ],
    },
    author='Giulio Librando',
    author_email='giuliolibrando@gmail.com',
    description='A tool to retrieve and display Slurm usage data',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/giuliolibrando/slurm-scredits',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
