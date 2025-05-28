# Canon Camera MCP

A minimal server for controlling Canon cameras via the Canon Camera Control API (CCAPI), using FastMCP for streamable HTTP transport.

#### Demo 🎥
[![IMAGE ALT TEXT](http://img.youtube.com/vi/59icGndauho/0.jpg)](http://www.youtube.com/watch?v=59icGndauho "Canon MCP Server Demo")

[LinkedIn Post](https://www.linkedin.com/posts/ishanjoshi99_claude-ai-canon-camera-ive-been-activity-7333390072735535104-Sl0b?utm_source=share&utm_medium=member_desktop&rcm=ACoAACE9cFEBBFrka0tZ6SOykeuUIa1qgqTv7WE)

## Features

- Control Canon cameras remotely via CCAPI.
- Expose camera functions over HTTP using FastMCP.
- Image compression and streaming support.

## Requirements

- Python 3.10+
- Canon camera with CCAPI enabled ([CCAPI activation guide](https://www.canon.com.au/apps/eos-digital-software-development-kit))
- See `requirements.txt` for Python dependencies.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Activate CCAPI on your Canon camera:**
   - Follow the official [Canon CCAPI activation instructions](https://www.canon.com.au/apps/eos-digital-software-development-kit).

3. **Configure camera IP:**
   - Set the `CANON_IP` environment variable to your camera’s IP address, or pass it as an argument.

## Usage

To run the server with Claude Desktop Client

```json
{
  "mcpServers": {
    "Canon Camera Controller": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/dir",
        "run",
        "server.py"
      ],
      "env": {
        "CANON_IP": "192.168.0.111"
      }
    }
  }
}
```

Or with plain Python:

```bash
python server.py
```

## References

- Based on [laszewsk/canon-r7-ccapi](https://github.com/laszewsk/canon-r7-ccapi)

## Project Structure

- `canon_camera.py`: Canon camera CCAPI interface.
- `server.py`: FastMCP HTTP server exposing camera controls.
- `requirements.txt`: Python dependencies.


## Extending the project
The license terms of CCAPI access do not permit sharing the API reference. 

Once you have access, it's quite straightforward to get it working. 

You may also refer to the Canon CCAPI Feature [list](https://developercommunity.usa.canon.com/s/article/CCAPI-Function-List)

