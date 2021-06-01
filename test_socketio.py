from blockchain_demo import create_app, socket_io
from flask_socketio import emit
import unittest
import coverage

cov = coverage.coverage(branch=True)
cov.start()
app = create_app()


@socket_io.on('custom_submit_transaction_event')
def on_submit_transaction(data_from_block: dict):
    if data_from_block['block_author'] is None:
        emit('error_alert', data_from_block['block_author'])
    else:
        emit('my_logs', {'msg': f'{data_from_block["block_author"]} added new transaction.'}, broadcast=True)


@socket_io.on('custom_mine_unconfirmed_transactions_event')
def on_mine_unconfirmed_transactions(block_miner: str):
    from blockchain_demo.main import blockchain
    blockchain.peers[block_miner] = {'id': 'example id',
                                     'queued_transactions': ['Transactions'],
                                     'chain': blockchain.chain}
    new_block_index = blockchain.mine_block(block_miner)
    if not new_block_index:
        emit('my_logs', {'msg': 'No transactions to mine'})
    else:
        emit('display_blockchain_to_all_peers', broadcast=True)
        emit('my_logs', {'msg': f'Block #{new_block_index} mined by {block_miner}!'}, broadcast=True)


@socket_io.on('custom_no_transactions_to_mine')
def on_no_transactions_to_mine(block_miner: str):
    from blockchain_demo.main import blockchain
    blockchain.peers[block_miner] = {'id': 'example id',
                                     'queued_transactions': [],
                                     'chain': blockchain.chain}
    new_block_index = blockchain.mine_block(block_miner)
    if not new_block_index:
        emit('my_logs', {'msg': 'No transactions to mine'})
    else:
        emit('display_blockchain_to_all_peers', broadcast=True)
        emit('my_logs', {'msg': f'Block #{new_block_index} mined by {block_miner}!'}, broadcast=True)


class TestSocketIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        cov.stop()
        # cov.report(show_missing=True)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ping(self):
        client = socket_io.test_client(app)
        client.get_received()
        client.emit('my_ping')
        received = client.get_received()
        self.assertEqual(received[0]['name'], 'my_pong')

    def test_peers_handler(self):
        client = socket_io.test_client(app)
        client.get_received()
        client.emit('peers_handler', 'username_example')
        received = client.get_received()
        self.assertEqual(len(received), 2)
        client.emit('peers_handler', '')
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'error_alert')

    def test_submit_transaction(self):
        client = socket_io.test_client(app)
        client.get_received()
        transaction_info = {'block_content': 'example text',
                            'block_author': None,
                            'author_id': 'id'
                            }
        client.emit('custom_submit_transaction_event', transaction_info)
        received = client.get_received()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'error_alert')

        transaction_info = {'block_content': 'example text',
                            'block_author': 'example author',
                            'author_id': 'id'
                            }
        client.emit('custom_submit_transaction_event', transaction_info)
        received = client.get_received()
        self.assertEqual(received[0]['name'], 'my_logs')

    def test_mine_unconfirmed_transactions(self):
        client = socket_io.test_client(app)
        client.emit('custom_no_transactions_to_mine', 'miner tester')
        received = client.get_received()
        self.assertEqual(received[0]['name'], 'my_logs')
        client.emit('custom_mine_unconfirmed_transactions_event', 'miner tester')
        received = client.get_received()
        self.assertEqual(received[0]['name'], 'display_blockchain_to_all_peers')
        self.assertEqual(received[1]['name'], 'my_logs')


if __name__ == '__main__':
    unittest.main()
