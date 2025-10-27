from app import create_app
from app.extensions import db

app = create_app()

local_host = 'localhost'
local_port = 5000

if __name__ == '__main__':
    app.run(host=local_host, port=local_port, debug=True)
