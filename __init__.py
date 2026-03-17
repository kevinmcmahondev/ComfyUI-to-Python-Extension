import sys
import os

from io import StringIO

import traceback

from aiohttp import web

ext_dir = os.path.dirname(__file__)
sys.path.append(ext_dir)

try:
    import black  # noqa: F401
except ImportError:
    raise ImportError(
        "Required package 'black' is not installed for ComfyUI-SaveAsScript. "
        "Please install it manually: pip install black"
    )

# Prevent reimporting of custom nodes
os.environ["RUNNING_IN_COMFYUI"] = "TRUE"

from comfyui_to_python import ComfyUItoPython  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(ext_dir)))

import server  # noqa: E402

WEB_DIRECTORY = "js"
NODE_CLASS_MAPPINGS = {}

MAX_WORKFLOW_SIZE = 10 * 1024 * 1024  # 10 MB


@server.PromptServer.instance.routes.post("/saveasscript")
async def save_as_script(request):
    try:
        if request.content_length and request.content_length > MAX_WORKFLOW_SIZE:
            return web.Response(text="Request too large", status=413)

        data = await request.json()

        if not isinstance(data, dict):
            return web.Response(text="Request body must be a JSON object", status=400)

        workflow = data.get("workflow")

        if not isinstance(workflow, str):
            return web.Response(text="Invalid or missing 'workflow' field", status=400)

        sio = StringIO()
        ComfyUItoPython(workflow=workflow, output_file=sio)

        sio.seek(0)
        result = sio.read()

        return web.Response(text=result, status=200)
    except Exception:
        traceback.print_exc()
        return web.Response(text="Internal server error", status=500)
