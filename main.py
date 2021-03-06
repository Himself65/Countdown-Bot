#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from cqhttp import CQHttp
from util import print_log
from global_vars import message_listeners, registered_commands, config, loop_threads, loaded_plugins, loop_threads, console_commands
from register import console_command
from flask import request, make_response
from json import JSONEncoder
import threading
import time
import pdb
import flask
import os
import importlib
import global_vars
# import PyV8
bot = CQHttp(api_root=config.API_URL, access_token=config.ACCESS_TOKEN)
log = bot.logger


def start():
    print_log("Starting countdown-bot.")
    print_log("By MikuNotFoundException.")
    print_log("QQ:814980678")
    global_vars.VARS["bot"] = bot
    global_vars.VARS["web_app"] = bot._server_app
    global_vars.CONFIG[__name__] = config

    def load_python_plugin(plugin):
        plugin_name = plugin[:plugin.index(".py")]
        if os.path.exists("./plugins/config/%s_config.py" % plugin_name):
            global_vars.CONFIG["plugins."+plugin_name] = importlib.import_module(
                "plugins.config."+plugin_name+"_config")
        elif os.path.exists("./plugins/config/%s_config_default.py" % plugin_name):
            global_vars.CONFIG["plugins."+plugin_name] = importlib.import_module(
                "plugins.config."+plugin_name+"_config_default")
        this = importlib.import_module("plugins."+plugin_name)
        if "plugin" in dir(this):
            loaded_plugins[plugin_name] = (dict(**this.plugin(), **{
                "load": getattr(this, "load", None),
                "disable": getattr(this, "disable", None),
                "name": plugin_name
            }))
            if hasattr(this, "load"):
                this.load()
            print_log("Loaded plugin: {}".format(loaded_plugins[plugin_name]))

    def load_javascript_plugin(name):
        pass
    # 加载插件
    for plugin in os.listdir("./plugins"):
        if os.path.isfile(os.path.join("./plugins", plugin)) == False:
            continue
        if plugin.startswith("__"):
            continue
        if plugin.endswith(".py"):
            load_python_plugin(plugin)
        elif plugin.endswith(".js"):
            load_javascript_plugin(plugin)
    print_log("Registered commands:\n{}".format("".join(
        map(lambda x: "{} :{}\n".format(x[0], x[1]), registered_commands.items()))))
    print_log("Registered message listeners:\n{}".format(message_listeners))
    print_log("Registered schedule loops:\n{}".format(loop_threads))
    for x in loop_threads:
        x.start()
    # 启动CQ Bot
    print_log("Starting CQHttp...")
    app_thread = threading.Thread(target=lambda: bot.run(
        host=config.POST_ADDRESS, port=config.POST_PORT))
    app_thread.start()
    global_vars.VARS["app_thread"] = app_thread
    input_loop()


@console_command(name="stop", help="关闭Bot")
def stop(args):
    import util
    import global_vars
    print_log("Shutting down schedule loops..")
    for x in global_vars.loop_threads:
        util.stop_thread(x)
    print_log("Shutting flask..")
    util.stop_thread(global_vars.VARS["app_thread"])
    exit(0)


@console_command(name="help", help="查看帮助")
def console_help(args):
    for k, v in console_commands.items():
        print_log("%s %s" % (k, v[0]))


@bot.on_message()
def handle_message(context):
    print_log("Handling message:{}".format(context))
    if "group_id" in context:
        text: str = None
        import cqhttp
        if type(context["message"]) is str:
            text = context["message"]
        elif context["message"][0]["type"] == "text":
            text: str = context["message"][0]["data"]["text"]

        def check_prefix(command):
            for item in config.COMMAND_PREFIX:
                if command.startswith(item):
                    return item
        prefix = check_prefix(text)
        if text is not None and prefix is not None:
            command = (text[len(prefix):]+" ").split(" ")
            print_log("Execute command: {}".format(command))
            if command[0] in registered_commands:
                from global_vars import last_command as last
                if context["group_id"] not in last:
                    last[context["group_id"]] = 0
                if (time.time()-last[context["group_id"]])*1000 < config.COMMAND_COOLDOWN:
                    bot.send(context, "指令冷却中.")
                    return
                else:
                    last[context["group_id"]] = time.time()
                registered_commands[command[0]][1].__call__(
                    bot, context, command)
            else:
                bot.send(context, "未知指令: %s" % command[0])
        if text is not None:
            print_log("Calling message listeners.")
            for listener in message_listeners:
                listener.__call__(bot, context, text)


@bot.on_request("group", "friend")
def handle_group_invite(context):
    return {"approve": True}


def input_loop():
    while True:
        args = (input(">")+" ").split(" ")
        if args[0] in console_commands:
            try:
                console_commands[args[0]][1](args)
            except Exception as ex:
                print_log(ex)
                raise ex
        else:
            print("Unknown command: {}".format(args))


if __name__ == "__main__":
    # pdb.set_trace()
    start()
