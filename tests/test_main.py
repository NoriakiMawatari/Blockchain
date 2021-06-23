from blockchain_demo.main import Block, BlockChain
from datetime import datetime
import pytest


def test_chain_route(client):
    response = client.get('/chain')
    assert response.status_code == 200
    assert b'chain' in response.data
    assert b"peers" in response.data


def test_add_new_transaction(client):
    transaction_data_example = {'content': 'example content',
                                'author_id': 'id'}
    response = client.post('/add_new_transaction', json=transaction_data_example)
    assert b"Invalid transaction data" in response.data


def test_block():
    block = Block(123, [], datetime.now(), 'hash_str_sample')
    assert isinstance(block, Block)
    block_hash = block.create_hash
    assert block_hash is not None


def test_blockchain():
    blockchain = BlockChain()
    assert isinstance(blockchain, BlockChain)


def test_genesis_block():
    blockchain = BlockChain()
    assert isinstance(blockchain.chain[0], Block)
    genesis_block = blockchain.chain[0]
    assert genesis_block.prev_hash == '0'


def peers_in_blockchain():
    blockchain = BlockChain()
    tester_peer = 'tester peer'
    blockchain.peers[tester_peer] = {'id': 'tester_id',
                                     'queued_transactions': [],
                                     'chain': blockchain.chain}
    assert tester_peer in blockchain.peers


@pytest.mark.parametrize(('transactions', 'author'), (
        ('This are some transactions', 'tester_author'),
        ('Some more transactions', None),
))
def test_add_transaction(transactions, author):
    blockchain = BlockChain()
    blockchain.peers[author] = {'id': 'tester_id',
                                'queued_transactions': [],
                                'chain': blockchain.chain}
    assert author in blockchain.peers
    transaction_info = {'content': transactions,
                        'author': author,
                        'author_id': blockchain.peers[author]['id']
                        }
    blockchain.add_transaction(transaction_info, author)
    tester_transactions = blockchain.peers[author]['queued_transactions']
    if author is None:
        assert transactions not in tester_transactions
    else:
        assert transactions in tester_transactions[0]['content']


def test_mine_block():
    blockchain = BlockChain()
    sample_transaction = 'Some queued transaction samples'
    blockchain.peers['tester'] = {'id': 'tester_id',
                                  'queued_transactions': [sample_transaction],
                                  'chain': blockchain.chain}
    blockchain.add_transaction(sample_transaction, 'tester')
    blockchain.mine_block('tester')
    assert len(blockchain.peers['tester']['chain']) == 2
    assert len(blockchain.chain) == 2


def test_proof_of_work():
    blockchain = BlockChain()
    block = Block(1, [], datetime.now(), 'hash_str_sample')
    proof = blockchain.proof_of_work(block)
    difficulty = blockchain.difficulty
    assert proof.startswith('0' * difficulty)


def test_add_multiple_blocks():
    blockchain = BlockChain()
    assert isinstance(blockchain, BlockChain)
    peer = 'Peer1'
    blockchain.peers[peer] = {'id': 'peer_id',
                              'queued_transactions': [],
                              'chain': blockchain.chain}
    assert peer in blockchain.peers
    transaction_info = {'content': '1st transaction text (Block#1)',
                        'author': peer,
                        'author_id': blockchain.peers[peer]['id']
                        }
    blockchain.add_transaction(transaction_info, peer)
    peer_transactions = blockchain.peers[peer]['queued_transactions']
    assert '1st transaction text (Block#1)' == peer_transactions[0]['content']
    blockchain.mine_block(peer)
    assert blockchain.peers[peer]['chain'][1].transactions[0]['content'] is '1st transaction text (Block#1)'

    # Adding second block
    transaction_info['content'] = '2nd transaction text (Block#2)'
    blockchain.add_transaction(transaction_info, peer)
    peer_transactions = blockchain.peers[peer]['queued_transactions']
    assert '2nd transaction text (Block#2)' == peer_transactions[0]['content']
    blockchain.mine_block(peer)
    assert blockchain.peers[peer]['chain'][2].transactions[0]['content'] is '2nd transaction text (Block#2)'


def test_multiple_transactions_in_block():
    blockchain = BlockChain()
    assert isinstance(blockchain, BlockChain)
    peer = 'Peer1'
    blockchain.peers[peer] = {'id': 'peer_id',
                              'queued_transactions': [],
                              'chain': blockchain.chain}
    assert peer in blockchain.peers
    first_transaction_info = {'content': '1st transaction text (Block#1)',
                              'author': peer,
                              'author_id': blockchain.peers[peer]['id']
                              }
    blockchain.add_transaction(first_transaction_info, peer)
    second_transaction_info = {'content': '2nd transaction text (Block#1)',
                               'author': peer,
                               'author_id': blockchain.peers[peer]['id']
                               }
    blockchain.add_transaction(second_transaction_info, peer)
    peer_transactions = blockchain.peers[peer]['queued_transactions']
    assert '1st transaction text (Block#1)' == peer_transactions[0]['content']
    assert '2nd transaction text (Block#1)' == peer_transactions[1]['content']
    blockchain.mine_block(peer)
    assert blockchain.peers[peer]['chain'][1].transactions[0]['content'] is '1st transaction text (Block#1)'
