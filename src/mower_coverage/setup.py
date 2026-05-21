from setuptools import find_packages, setup

package_name = 'mower_coverage'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/coverage.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Laura',
    maintainer_email='seu_email@exemplo.com',
    description='Algoritmos de cobertura de área pro robô cortador de grama',
    license='MIT',
    entry_points={
        'console_scripts': [
            'random_coverage = mower_coverage.random_coverage:main',
        ],
    },
)
