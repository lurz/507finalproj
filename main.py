import flask
app = flask.Flask(__name__)

@app.route('/')
def hello_world():
    navigation = [{'href': 'aaa', 'caption': 'number 1'}]
    context = {'navigation': navigation}
    return flask.render_template("index.html", **context)