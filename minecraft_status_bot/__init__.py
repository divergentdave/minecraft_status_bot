#!/usr/bin/env python3
import mcstatus
import requests
import slacker
import time
import uuid
import yaml

class MinecraftServer:
    def __init__(self, ip):
        self.ip = ip

    def run(self):
        server = mcstatus.MinecraftServer.lookup(self.ip)
        response = server.status()
        return response.description["text"], response.players.online

class RealmsDirectory:
    AUTH_URL = "https://authserver.mojang.com/authenticate"
    WORLDS_URL = "https://mcoapi.minecraft.net/worlds"
    JOIN_URL = "https://mcoapi.minecraft.net/worlds/{}/join"

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

    def list(self):
        if not self.cookies:
            self.login()
        worlds_response = requests.get(self.WORLDS_URL, cookies=self.cookies)
        worlds_body = worlds_response.json()
        for server in worlds_body["servers"]:
            join_response = requests.get(self.JOIN_URL.format(server["id"]),
                                         cookies=self.cookies)
            join_body = join_response.json()
            yield MinecraftServer(join_body["address"])


def main():
    config = yaml.load(open("config.yaml"))
    servers = []
    config_minecraft = config["minecraft"]
    if "ip" in config_minecraft:
        for ip in config_minecraft["ip"]:
            servers.append(MinecraftServer(ip))
    if "realms" in config_minecraft:
        config_realms = config_minecraft["realms"]
        if "username" in config_realms and "password" in config_realms:
            directory = RealmsDirectory(config_realms["username"],
                                        config_realms["password"])
            for server in directory.list():
                servers.append(server)

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
            name, count = server.run()
            last_count = last_counts.get(server.ip, 0)
            if last_count < threshold and count >= threshold:
                msg = "Beep boop, there are {} players on {}".format(
                    count,
                    name
                )
                print(msg)
                slack.chat.post_message(channel, msg)
            last_counts[server.ip] = count
        time.sleep(5 * 60)
