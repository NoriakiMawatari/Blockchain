# Blockchain Demo
A simple demo of blockchain concepts in Python based on micro-framework [Flask](https://flask.palletsprojects.com/en/2.0.x/tutorial/factory/) 
and [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/#) in order to enable client-server communications.


## Instructions to run
Clone the project
```sh
$ git clone https://github.com/NoriakiMawatari/Blockchain.git
```
Once located on the Blockchain directory, create a virtual environment,
```sh
$ cd Blockchain
$ python -m venv venv
```
Make sure to activate the virtual environment,
```sh 
$ source venv/bin/activate
```
Install the dependencies,
```sh
$ pip install -r requirements.txt
```

Finally, run the following command: 
```sh
(venv) $ python run.py
```

### Run tests
```shell
(venv) $ python -m pytest
```

In order to visualize each test instead of only displaying dots, you can run:
```sh
(venv) $ python -m pytest -v
```