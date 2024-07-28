from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'RisingOS dummy websever just to keep service healty'

if __name__ == "__main__":
    app.run()