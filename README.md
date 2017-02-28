# minecraft\_status\_bot

This is a Slack bot script that watches any number of Minecraft servers (Realms or standalone) and posts in a Slack channel when some number of people are online.

## Installing

You need to have [Python 3](https://www.python.org/) installed first. Clone this repository, then run `python3 setup.py` from the top directory to install the script and its other dependencies.

## Configuring

Copy the file `config.yaml.example` into `config.yaml` and follow the instructions to fill it in. You can mix and match standalone Minecraft servers with Realms servers, or you can delete either section if you don't want to use it. You will need to get a Slack API token, I used the [Slack API Tester](https://konklone.slack.com/apps/A02-slack-api-tester) for this.

## Running

Run the script with `minecraft_status_bot` or `python3 -m minecraft_status_bot`. It will start checking the servers every five minutes. Whenever it sends a message to Slack, it will also print to STDOUT. Running as a service is left as an exercise for the reader.
