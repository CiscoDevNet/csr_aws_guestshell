from distutils.core import setup
setup(
    name='csr_aws_guestshell',
    packages=[setup.name],  # this must be the same as the name above
    version='0.0.1',
    description='A helper library for Cisco guestshell on AWS',
    author='Christopher Reder',
    author_email='creder@cisco.com',
    scripts=["bin/get-metadata.py", "bin/get-route-table.py"],
    # use the URL to the github repo
    url='https://github.com/CiscoDevNet/' + setup.name,
    packages=["csr_aws_guestshell"],
    download_url='https://github.com/CiscoDevNet/' + setup.name + '/archive/' + \
        setup.version + '.tar.gz',
    keywords=['cisco', 'aws', 'guestshell'],
    classifiers=[],
    license = "MIT",
    install_requires=[
        'boto',
        'boto3',
    ],
)
