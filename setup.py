from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in parason_customization/__init__.py
from parason_customization import __version__ as version

setup(
	name="parason_customization",
	version=version,
	description="parason-customization",
	author="Aerele Technologies",
	author_email="hello@aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
