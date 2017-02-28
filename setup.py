from setuptools import setup

setup(
    name="minecraft_status_bot",
    version="0.0.1",
    description="Slack bot that polls a Minecraft server's status and posts when people are playing",
    author="David Cook",
    author_email="divergentdave@gmail.com",
    packages=["minecraft_status_bot"],
    install_requires=[
        "mcstatus",
        "pyyaml",
        "requests",
        "slacker",
    ],
    entry_points = {
        "console_scripts": ["minecraft_status_bot=minecraft_status_bot:main"]
    }
)
