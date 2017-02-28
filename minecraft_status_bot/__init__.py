#!/usr/bin/env python3
import mcstatus
import requests
import slacker
import time
import uuid
import yaml

class MinecraftServer:
    pass

class IPMinecraftServer(MinecraftServer):
    def __init__(self, ip):
        self.ip = ip

    def run(self):
        server = mcstatus.MinecraftServer.lookup(self.ip)
        response = server.status()
        yield response.description["text"], response.players.online, self.ip

class RealmsMetaServer(MinecraftServer):
    AUTH_URL = "https://authserver.mojang.com/authenticate"
    WORLDS_URL = "https://mcoapi.minecraft.net/worlds"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client_token = str(uuid.uuid4())
        self.cookies = {}

    def login(self):
        auth_payload = {
            "agent": {
                "name": "Minecraft",
                "version": 1
            },
            "username": self.username,
            "password": self.password,
            "clientToken": self.client_token
        }
        auth_response = requests.post(self.AUTH_URL, json=auth_payload)
        auth_body = auth_response.json()
        access_token = auth_body["accessToken"]
        assert self.client_token == auth_body["clientToken"]
        if self.client_token != auth_body["clientToken"]:
            raise Exception("Yggdrasil server did not echo back clientToken"
                            "\n\n{}".format(auth_body))

        player_uuid = auth_body["selectedProfile"]["id"]
        player_name = auth_body["selectedProfile"]["name"]
        self.cookies = {
            "sid": "token:{}:{}".format(access_token, player_uuid),
            "user": player_name,
            "version": "1.11.2"
        }

    def run(self):
        if not self.cookies:
            self.login()
        worlds_response = requests.get(self.WORLDS_URL, cookies=self.cookies)
        worlds_body = worlds_response.json()
        for server in worlds_body["servers"]:
            num_players = 0
            if server["players"] is not None:
                num_players = len(server["players"])
            yield server["name"], num_players, server["id"]


def main():
    config = yaml.load(open("config.yaml"))
    servers = []
    config_minecraft = config["minecraft"]
    if "ip" in config_minecraft:
        for ip in config_minecraft["ip"]:
            servers.append(IPMinecraftServer(ip))
    if "realms" in config_minecraft:
        config_realms = config_minecraft["realms"]
        if "username" in config_realms and "password" in config_realms:
            servers.append(RealmsMetaServer(config_realms["username"],
                                            config_realms["password"]))

    if not servers:
        raise Exception("No server details were specified. Please edit "
                        "config.yaml and add either a server IP address or "
                        "login credentials for checking Minecraft Realms")

    config_slack = config["slack"]
    slack = slacker.Slacker(config_slack["token"])
    channel = config_slack["channel"]

    threshold = config["threshold"]
    last_counts = {}
    while True:
        for server in servers:
            for name, count, identifier in server.run():
                last_count = last_counts.get(identifier, 0)
                if last_count < threshold and count >= threshold:
                    msg = "Beep boop, there are {} players on {}".format(
                        count,
                        name
                    )
                    print(msg)
                    slack.chat.post_message(channel, msg)
                last_counts[identifier] = count
        time.sleep(5 * 60)
