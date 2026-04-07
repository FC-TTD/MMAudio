from argparse import ArgumentParser

import uvicorn

from mmaudio.api_app import app


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', type=int, default=7860)
    args = parser.parse_args()
    uvicorn.run(app, host='0.0.0.0', port=args.port)
