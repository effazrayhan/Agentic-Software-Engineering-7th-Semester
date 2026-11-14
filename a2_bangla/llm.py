import json
import urllib.request


def _default_transport(url, data, headers, timeout):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    class _Resp:
        def read(self_inner):
            return body
    return _Resp()


class OllamaClient:
    """Minimal Ollama /api/chat client with injectable transport."""

    def __init__(
        self,
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        transport=None,
        timeout=120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.transport = transport or _default_transport
        self.timeout = timeout

    def chat(self, messages, tools=None, options=None, keep_alive=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = tools
        if options is not None:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive

        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        resp = self.transport(
            f"{self.base_url}/api/chat",
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        body = resp.read()
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8")
        return json.loads(body)
