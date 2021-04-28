from flask import Flask

app = Flask(__name__)
app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'blockchain_app.sqlite'),
    )


# a simple page that says hello
@app.route('/hello')
def hello():
    return 'Hello, World!'


from blockchain_app import views
