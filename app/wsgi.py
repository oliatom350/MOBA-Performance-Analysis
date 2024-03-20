from flask import Flask, request, jsonify
from markupsafe import escape

app = Flask(__name__)


@app.route('/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'User {escape(username)}'


@app.route('/', methods=['POST', 'GET'])
def hello():
    if request.method == 'GET':
        return '<p>Hello, World. This is GET request</p>'
    else:
        return '<p>Hello, World. This is POST request</p>'


@app.route('/api/data')
def get_data():
    data = {'message': 'Hello from Flask!'}
    return jsonify(data)


if __name__ == '__main__':
    app.run()
