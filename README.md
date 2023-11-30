# DEPRECATION NOTICE

## This project is not maintained anymore

The main goal of this project was to fix the connection stability bugs I had with the native API, by using a mature battle tested server framework, in this case - Flask. The default API was using low level python HTTP Server library, which, in my case, was not working well over a VPN connection, it was unstable compared to my reimplementation.

However now Text Generation Web UI deprecated their old API in favor of making the OpenAI API (or OpenedAPI as they call it) the default one. It's using FastAPI at it's core, which is also a good stable and popular framework that can be trusted to work reliably.

The added bonus is that this API is compatible with OpenAI API, which allows a plethora of other tools to connect to textgen instead of OpenAI, which is great.

The new API also has all the features of the old one and more. 

So, with all that said, this project is not needed anymore. 


# ooba_flask_api

This is a drop-in replacement for the built-in API.

In my testing while using API remotely over VPN tunnel I was getting various broken pipe and broken chunk errors.

I decide to try and reimplement API using Flask. So far it seems to be more stable.

To install it `git clone` this repo into `extensions` folder of ooba text-generation-webui.

Then enable it by adding `--extensions ooba_flask_api` to launch arguments.

This extension is still experimental. 
