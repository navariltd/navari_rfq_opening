from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in rfq_opening_process/__init__.py
from rfq_opening_process import __version__ as version

setup(
	name="rfq_opening_process",
	version=version,
	description="Customization on RFQ and Supplier Quotation Opening process.",
	author="Navari Limited",
	author_email="info@navari.co.ke",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
