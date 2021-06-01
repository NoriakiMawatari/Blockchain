# Blockchain Demo
A simple demo of a blockchain concepts in Python based on micro-framework [Flask](https://flask.palletsprojects.com/en/2.0.x/tutorial/factory/) 
and [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/#) module in order to enable communications between 
clients and a server.


## Instructions to run
Clone the project
```sh
$ git clone https://github.com/NoriakiMawatari/Blockchain.git
```
Install the dependencies,

```sh
$ cd Blockchain
$ pip install -r requirements.txt
```

Make sure to activate a virtual environment,

```sh 
$ source venv/bin/activate
```

Finally, run the following command: 
```sh
(venv) $ python run.py
```

### Run tests
```shell
(venv) $ pytest
```

In order to visualize each test instead of only displaying dots, you can run:
```sh
(venv) $ pytest -v
```