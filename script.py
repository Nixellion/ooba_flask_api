ASYNC_MODE = "threading"  # gevent, eventlet will break ooba, as they monkey patch the whole thing. Might work with multiprocessing.

# if ASYNC_MODE == 'eventlet':
#     import eventlet
#     eventlet.monkey_patch()
    
# elif ASYNC_MODE == "gevent":
#     from gevent import monkey
#     monkey.patch_all()

import uuid
from flask import Flask, jsonify, request
from flask_socketio import SocketIO

import json
from threading import Thread

from extensions.api.util import build_parameters, try_start_cloudflared
from modules import shared
from modules.chat import generate_chat_reply
from modules.LoRA import add_lora_to_model
from modules.models import load_model, unload_model
from modules.text_generation import (encode, generate_reply,
                                     stop_everything_event)
from modules.utils import get_available_models
from server import get_model_specific_settings, update_model_parameters

app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid.uuid4())

socketio = SocketIO(app, async_mode=ASYNC_MODE)

def add_background_task(task, interval):
    def tsk():
        while True:
            try:
                print(f"Running background task {task.__name__}...")
                task()
                print(f"Completed background task {task.__name__}!")
            except Exception as e:
                print(f"Can't run background task '{task.__name__}': {e}", exc_info=True)
            socketio.sleep(interval)

    socketio.start_background_task(tsk)


def get_model_info():
    return {
        'model_name': shared.model_name,
        'lora_names': shared.lora_names,
        # dump
        'shared.settings': shared.settings,
        'shared.args': vars(shared.args),
    }

@app.route("/v1/model", methods=["GET", "POST"])
@app.route("/api/v1/model", methods=["GET", "POST"])
def model():
    if request.method == "GET":
        return jsonify({
                    'result': shared.model_name
                })
    else:
        body = request.json

         # by default return the same as the GET interface
        result = shared.model_name

        # Actions: info, load, list, unload
        action = body.get('action', '')

        if action == 'load':
            model_name = body['model_name']
            args = body.get('args', {})
            print('args', args)
            for k in args:
                setattr(shared.args, k, args[k])

            shared.model_name = model_name
            unload_model()

            model_settings = get_model_specific_settings(shared.model_name)
            shared.settings.update(model_settings)
            update_model_parameters(model_settings, initial=True)

            if shared.settings['mode'] != 'instruct':
                shared.settings['instruction_template'] = None

            try:
                shared.model, shared.tokenizer = load_model(shared.model_name)
                if shared.args.lora:
                    add_lora_to_model(shared.args.lora) # list

            except Exception as e:
                response = {'error': { 'message': repr(e) } }
                return jsonify(response)

            shared.args.model = shared.model_name

            result = get_model_info()

        elif action == 'unload':
            unload_model()
            shared.model_name = None
            shared.args.model = None
            result = get_model_info()

        elif action == 'list':
            result = get_available_models()

        elif action == 'info':
            result = get_model_info()

        response = {
            'result': result,
        }

        return jsonify(response)

@app.route("/v1/generate", methods=['POST'])
@app.route("/api/v1/generate", methods=['POST'])
def generate():
    prompt = request.json['prompt']
    print(f"/api/v1/generate: {prompt[0:80]}")
    generate_params = build_parameters(request.json)
    stopping_strings = generate_params.pop('stopping_strings')
    generate_params['stream'] = False

    generator = generate_reply(
        prompt, generate_params, stopping_strings=stopping_strings, is_chat=False)

    answer = ''
    for a in generator:
        answer = a

    response = {
        'results': [{
            'text': answer
        }]
    }
    print(f"/api/v1/generate FINISHED: {prompt[0:80]}")
    return jsonify(response)

@app.route("/v1/stop-stream", methods=['POST'])
@app.route("/api/v1/stop-stream", methods=['POST'])
def stop_stream():
    stop_everything_event()

    response = {
        'results': 'success'
    }

    return jsonify(response)

@app.route("/v1/token-count", methods=['POST'])
@app.route("/api/v1/token-count", methods=['POST'])
def token_count():
    tokens = encode(request.json['prompt'])[0]
    response = {
        'results': [{
            'tokens': len(tokens)
        }]
    }

    return jsonify(response)

def _run_server():
    try:
        address = '0.0.0.0' if shared.args.listen else '127.0.0.1'
        port = 5002
        print(f"Flask API running at http://{address}:{port}")
        socketio.run(app, host=address, port=port)
    except:
        print("Unable to start", exc_info=True)

def setup():
    thread = Thread(target=_run_server)
    thread.start()
    
