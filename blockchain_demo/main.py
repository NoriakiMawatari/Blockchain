import json
from datetime import datetime
from hashlib import sha256
from typing import List, Any, Callable

import requests
from flask import Blueprint, redirect, render_template, request
from flask_socketio import emit

from blockchain_demo import socket_io

main = Blueprint('main', __name__)


class Block:
    """
    Block object instance.

    Contains key information in order to be stored. Also these blocks have certain storage capacities and, when filled,
    are chained onto the previously filled block, forming a chain of data known as the 'blockchain'.

    Parameters
    ----------
    index : int
        Position the block has in the blockchain.
    transactions: List[Any]
        It can be any kind of information, in this project we use the 'transaction' concept to simulate a
        cryptocurrency application.
    timestamp: datetime
        Record of when block was created.
    prev_hash: str
        This is the hash of the former block in chain.
    nonce: int
        Number of times the hash was calculated to accomplish the difficulty constrain and become a valid hash.
    """
    def __init__(self, index: int, transactions: List[Any], timestamp: datetime, prev_hash: str, nonce: int = 0) -> None:
        self.index = index
        self.timestamp = str(timestamp)
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = nonce

    @property
    def create_hash(self) -> str:
        """
        str: This may look like a chunk of random alphanumeric values that uniquely identifies the data inside called
        hash.

        Notes
        -----
        create_hash property generates a unique hash using the information that compose the block.
        Based on the following hashing function:

        .. math:: f( index + previous hash + timestamp + data + nonce ) = hash

        Hashing is a fundamental part of the block creation, because with the minimal change in data leads to a large
        change in resulting hash.
        """
        unique_block_string = json.dumps(self.__dict__, sort_keys=True)
        block_hash = sha256(unique_block_string.encode("utf-8")).hexdigest()
        return block_hash


class BlockChain:
    """
    Blockchain object instance.

    Kind of database built by blocks that are linked by a previous and actual hash. The essence of
    the blockchain is the immutability or irreversible timeline of data when implemented in a decentralized nature.
    That means, when a block is filled it can't be removed or changed.

    Attribute
    ----------
    difficulty: int
        For this blockchain demo three zeros at beginning of hash are required to approve a hash.
    """
    difficulty = 3

    def __init__(self):
        self.chain = []
        """list: Blocks container."""

        self.peers = {}
        """dict: Peers information container"""

        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Notes
        -----
        By instantiating a Blockchain object, a genesis block (Block #0) is created and added to chain list.
        """
        genesis_block = Block(0, [], datetime.now(), "0")
        genesis_block.hash = self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)

    def proof_of_work(self, block: Block) -> str:
        """
        Blockchain class method that iterates over the hash until the difficulty constrain is satisfied.
        Parameter
        --------
        block:
            Block's information to apply the proof of work.

        Returns
        -------
        Valid/acceptable hash.
        """
        acceptable_hash = block.create_hash
        while not acceptable_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            acceptable_hash = block.create_hash
        return acceptable_hash

    def is_valid_pow(self, block: Block, proof: str) -> bool:
        """
        This method verify if block.hash is a valid hash, satisfying difficulty constrain.

        Parameters
        ----------
        block:
            Block where hash is going to be evaluated.
        proof:
            Hash which meets the difficulty constraint.

        Returns
        ------
        bool:
            True if successful, false otherwise.
        """
        return proof.startswith('0' * self.difficulty) and proof == block.create_hash

    @property
    def get_latest_block(self) -> Block:
        """
        Block: `Block` object.

        Notes
        -----
        Property to get latest block in the `chain` attribute.
        """
        return self.chain[-1]

    @property
    def get_total_blocks(self) -> int:
        """
        int: Number of blocks into the blockchain.

        Notes
        -----
        Property to get the length of `chain` attribute.
        """
        return len(self.chain)

    def add_block_to_peer_chain(self, block: Block, proof: str, block_miner: str) -> bool:
        """
        Using the latest block in our `blockchain` an its hash, a block is added to the specific peer chain.

        Parameters
        ----------
        block:
            Block to be added into the blockchain.
        proof:
            Hash which meets the difficulty constraint.
        block_miner:
            Miner of the unique Block.
        Returns
        -------
        bool:
            True if successful, false otherwise.
        """
        last_block = self.get_latest_block
        prev_hash = last_block.hash

        if last_block.index + 1 != block.index:
            return False
        elif prev_hash != block.prev_hash:
            return False
        elif not self.is_valid_pow(block, proof):
            return False
        else:
            block.hash = proof
            self.peers[block_miner]['chain'].append(block)
            return True

    def add_transaction(self, transaction: str, author: str) -> None:
        """
        Transaction data is added to a queued_transactions list. Each peer has his own list, by giving the author
        argument we ensure its stored by that specific peer.

        Parameters
        ----------
        transaction:
            Data content as a transaction.
        author:
            Transaction's author.
        """
        if author:
            self.peers[author]['queued_transactions'].append(transaction)

    def mine_block(self, block_miner: str) -> int:
        """
        Parameter
        --------
        block_miner:
            Miner/author of the block's transactions.

        Returns
        -------
        int:
            Block's position on the blockchain.

        Notes
        -----
        The process of determining the block's nonce is called 'mining'. By the proof_of_work method we start with a
        nonce of 0 and keep incrementing it by 1 until it finds the valid hash. The block_miner is the name of that peer
        who is mining his own queued_transactions, adding them to a Block and executing the Proof of Work.
        Then if everything goes well, that block is added to peer's chain and the queued_transactions list is cleaned.
        """

        miner_queued_transactions = self.peers[block_miner]['queued_transactions']
        if not miner_queued_transactions:
            return False

        last_block = self.get_latest_block
        new_block = Block(index=last_block.index + 1,
                          transactions=miner_queued_transactions,
                          timestamp=datetime.now(),
                          prev_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        self.add_block_to_peer_chain(new_block, proof, block_miner)
        self.peers[block_miner]['queued_transactions'] = []
        return new_block.index


blockchain = BlockChain()
queued_transactions = []


@main.route('/chain', methods=['GET'])
def get_chain() -> json:
    """User can visits this url to visualize the blockchain content in JSON format."""
    chain_info = []
    for block in blockchain.chain:
        chain_info.append(block.__dict__)
    return json.dumps({"length": len(chain_info),
                       "chain": chain_info,
                       "peers": [peer for peer in blockchain.peers.keys()]})


@main.route('/queued_transactions/<peer_name>')
def get_queued_transactions(peer_name: str) -> json:
    queued_transactions_per_user = blockchain.peers[peer_name]['queued_transactions']
    return json.dumps(queued_transactions_per_user)


def fetch_queued_transactions() -> None:
    """This function uses the information stored in a chain route to collect transactions per block in a global list
    that is going to be parsed by the web app. """
    try:
        response = requests.get(f"{request.host_url}chain")
        if response.status_code == 200:
            transactions_to_fetch = []
            chain_content = json.loads(response.content)
            for block in chain_content["chain"]:
                for transaction in block["transactions"]:
                    transaction["index"] = block["index"]
                    transaction["hash"] = block["prev_hash"]
                    transactions_to_fetch.append(transaction)
            global queued_transactions
            queued_transactions = sorted(transactions_to_fetch, key=lambda key: key['timestamp'], reverse=False)
    except requests.exceptions.ConnectionError as error:
        error.status_code = "Connection to /chain refused"


@main.route('/')
def blockchain_index():
    fetch_queued_transactions()
    return render_template('index.html',
                           title='My Blockchain Demo',
                           readable_time=datetime.now(),
                           transactions=queued_transactions,
                           chain=blockchain.chain,
                           peers=blockchain.peers,)


@socket_io.event
def my_ping() -> None:
    """This event is called by each client and send a "pong" message so the round trip time is measured.
    When the pong is received, the time from the ping is stored, and the average of the last 30 samples is average and
    displayed by jQuery section in the base.html file."""
    emit('my_pong')


@socket_io.event
def peers_handler(peer_name: str) -> None:
    """This event handler the peer_name input and evaluates if it is acceptable. Whether it is, then name is added to
    the peers dictionary and a unique session id is given to it, also the queued_transactions list and a copy of the
    current blockchain.

    The broadcast_peer_status is emitted in order to communicate other online peers that a new peer is active."""
    if peer_name in [peer for peer in blockchain.peers.keys()] or peer_name == '':
        emit('error_alert', peer_name)
    else:
        blockchain.peers[peer_name] = {'id': request.sid,
                                       'queued_transactions': [],
                                       'chain': blockchain.chain}
        emit('display_peer_info', peer_name)
        emit('broadcast_peers_status', peer_name, broadcast=True)


@socket_io.event
def submit_transaction(block_data: dict):
    """Event that receives transaction information from transaction form in application and stores it in JSON object."""
    try:
        if block_data['block_author'] is None:
            emit('error_alert', block_data['block_author'])
        transaction_info = {'content': block_data['block_text'],
                            'author': block_data['block_author'],
                            'author_id': blockchain.peers[block_data['block_author']]['id']
                            }

        add_new_transaction_url = f"{request.host_url}add_new_transaction"
        requests.post(add_new_transaction_url,
                      json=transaction_info,
                      headers={'Content-type': 'application/json'})
        emit('my_logs', {'msg': f'{block_data["block_author"]} added new transaction.'}, broadcast=True)
        return redirect('/')
    except requests.exceptions.ConnectionError as error:
        error.status_code = "Connection to /add_new_transaction refused"


@main.route('/add_new_transaction', methods=['POST'])
def add_new_transaction():
    """In this endpoint, transaction information is reviewed and added to blockchain."""
    transaction_data = request.get_json()
    required_fields = ['author', 'content', 'author_id']

    for field in required_fields:
        if not transaction_data.get(field):
            return "Invalid transaction data", 404

    transaction_data['timestamp'] = str(datetime.now())
    blockchain.add_transaction(transaction_data, transaction_data['author'])
    return "Success", 201


@socket_io.event()
def mine_unconfirmed_transactions(block_miner: str) -> Callable[[Any, Any, bool], Any]:
    """Event that responds to a 'Mine Block' button in application, broadcast a message to all active peers of mined
     block in the Logs section."""
    new_block_index = blockchain.mine_block(block_miner)
    if not new_block_index:
        emit('my_logs', {'msg': 'No transactions to mine'})
    else:
        emit('display_blockchain_to_all_peers', broadcast=True)
        return emit('my_logs', {'msg': f'Block #{new_block_index} mined by {block_miner}!'}, broadcast=True)
