from setuptools import setup, find_packages


setup(
    name="pubsub_proxy",
    version="0.0.1",
    description="A Libra pub/sub proxy",
    python_requires=">=3.7",
    platforms=["POSIX"],
    zip_safe=True,
    packages=find_packages(),
    url="https://github.com/calibra/pubsub-proxy",
    install_requires=["ivtjfchcukjgtekjrnbllkfrdkvdhdkh>=0.2.20200401"],
    test_suite="wallet_tests",
    extras_require={
        "dev": [
            "pytest",
            "unittest-data-provider",
            "black",
            "bandit",
            "pyroma",
            "flake8",
        ],
    },
)
