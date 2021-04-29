from blockchain_app import app
from flask import render_template, redirect, request
import datetime
import json
import requests
from datetime import datetime
from hashlib import sha256


class Block:
    """Block class to define its content"""
    def __init__(self, index, transactions, timestamp, prev_hash):
        self.index = index
        self.timestamp = str(timestamp)
        self.transactions = transactions
        self.prev_hash = prev_hash

    def create_hash(self):
        unique_block_string = json.dumps(self.__dict__, sort_keys=True)
        block_hash = sha256(unique_block_string.encode("utf-8")).hexdigest()
        return block_hash


class BlockChain:
    difficulty = 3

    def __init__(self):
        self.chain = []
        self.queued_transactions = []
        self.genesis_block()

    def genesis_block(self):
        gen = Block(0, [], datetime.now(), "0")
        gen.hash = self.proof_of_work(gen)
        print(f"Genesis hash: {gen.hash}")
        print(f"Genesis prev_hash: {gen.prev_hash}")
        self.chain.append(gen)

    def proof_of_work(self, block):
        """This function iterates over the hash until the difficulty constrain is satisfied."""
        block.nonce = 0
        acceptable_hash = block.create_hash()
        while not acceptable_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            acceptable_hash = block.create_hash()
        return acceptable_hash

    def is_valid_pow(self, block, proof):
        """Verify if block.hash is a valid hash, satisfying difficulty constrain"""
        return proof.startswith('0' * self.difficulty) and proof == block.create_hash()

    def add_to_chain(self, block, proof):
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
            self.chain.append(block)
            return True

    def add_transaction(self, transaction):
        self.queued_transactions.append(transaction)

    def mine(self):
        """UI to add queued transactions to BlockChain adding them to a Block and executing the Proof of Work"""
        if not self.queued_transactions:
            return False

        last_block = self.get_latest_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.queued_transactions,
                          timestamp=datetime.now(),
                          prev_hash=last_block.hash)
        proof = self.proof_of_work(new_block)
        print(f"New block prev_hash: {new_block.prev_hash}")
        print(f"New block hash: {proof}")
        self.add_to_chain(new_block, proof)
        self.queued_transactions = []
        return new_block.index

    @property
    def get_latest_block(self):
        return self.chain[-1]

    @property
    def get_total_blocks(self):
        return len(self.chain)


blockchain = BlockChain()
peers = set()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required_fields = ['author', 'content']

    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404

    data['timestamp'] = str(datetime.now())
    blockchain.add_transaction(data)
    return "Success", 201


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_info = []
    for block in blockchain.chain:
        chain_info.append(block.__dict__)
    return json.dumps({"length": len(chain_info),
                       "chain": chain_info})


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        chain_len = len(blockchain.chain)
        updated_chain()
        if chain_len == len(blockchain.chain):
            announce_new_block(blockchain.get_latest_block)
        return f"Block #{result} mined"


@app.route('/queued_transactions')
def get_queued_transactions():
    return json.dumps(blockchain.queued_transactions)


@app.route('/add_peers', methods=['POST'])
def add_peer():
    nodes = request.get_json()
    print(f"\nNodes in add_peer: {nodes}")
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)
    print(peers)
    print(type(peers))
    return "Success", 201


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        return redirect('index.html')
    else:
        return render_template('login.html')


def updated_chain():
    global blockchain
    longest_chain = None
    chain_len = len(blockchain.chain)

    for node in peers:
        response = request.get(f'https://{node}/chain')
        node_len = response.json()['length']
        chain = response.json()['chain']
        if node_len > chain_len:
            chain_len = node_len
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True
    return False


@app.route('/add_block_p2p', methods=['POST'])
def validate_and_add_block():
    data = request.get_json()
    block = Block(data["index"],
                  data["transactions"],
                  data["timestamp"],
                  data["prev_hash"])
    proof = data["hash"]
    added = blockchain.add_to_chain(block, proof)

    if not added:
        return "Block was discarded by node", 400
    return "Block added to chain", 201


def announce_new_block(block):
    for peer in peers:
        url = f"https:://{peer}/add_block_p2p"
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


# The node with which our application interacts, there can be multiple such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:5000"
posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = f"{CONNECTED_NODE_ADDRESS}/chain"
    print(f"\nChain ADDRESS {get_chain_address}")
    response = requests.get(get_chain_address)
    print(f"\nResponse for the chain address gotten {response}")
    print(f"\nResponse content: {response.content}")
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        print(f"\nChain {chain}")
        for block in chain["chain"]:
            for transaction in block["transactions"]:
                transaction["index"] = block["index"]
                transaction["hash"] = block["prev_hash"]
                content.append(transaction)
        global posts
        posts = sorted(content, key=lambda key: key['timestamp'], reverse=False)
        print(f"\nPosts: {posts}")
        return chain


@app.route('/')
def home_page():
    chain = fetch_posts()
    print(f"THIS IS CHAIN: {chain}")
    return render_template('index.html',
                           title='Nori Blockchain',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=datetime.now(),
                           bc=blockchain,
                           chain=chain['chain']
                           )


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["block_data"]
    author = request.form["peer"]

    post_object = {
        'author': author,
        'content': post_content,
    }

    # Submit a transaction
    new_transaction_address = f"{CONNECTED_NODE_ADDRESS}/new_transaction"

    requests.post(new_transaction_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return redirect('/')


# def timestamp_to_string(epoch_time):
#     return epoch_time.strftime('%H:%M')

