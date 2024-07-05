from setuptools import setup, find_packages

setup(
    name='scredits',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',  # Assicurati di elencare tutte le dipendenze necessarie
    ],
    entry_points={
        'console_scripts': [
            'scredits = scredits.cli:main',
        ],
    },
)
