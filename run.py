from blockchain_demo import create_app, socket_io

app = create_app()

if __name__ == "__main__":
    socket_io.run(app, port=5000)
