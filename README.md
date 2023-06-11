# ooba_flask_api

This is a drop-in replacement for the built-in API.

In my testing while using API remotely over VPN tunnel I was getting various broken pipe and broken chunk errors.

I decide to try and reimplement API using Flask. So far it seems to be more stable.

To install it `git clone` this repo into `extensions` folder of ooba text-generation-webui.

Then enable it by adding `--extensions ooba_flask_api` to launch arguments.

This extension is still experimental. 