import hashlib
import json
import os
from datetime import datetime


# =========================================================
# BLOCK
# =========================================================

class Block:

    def __init__(
        self,
        index,
        timestamp,
        certificate_id,
        certificate_hash,
        previous_hash
    ):

        self.index = index

        self.timestamp = timestamp

        self.certificate_id = certificate_id

        self.certificate_hash = certificate_hash

        self.previous_hash = previous_hash

        self.hash = self.calculate_hash()


    # =====================================================
    # CALCULATE HASH
    # =====================================================

    def calculate_hash(self):

        block_data = (

            str(self.index)

            + str(self.timestamp)

            + self.certificate_id

            + self.certificate_hash

            + self.previous_hash

        )


        return hashlib.sha256(
            block_data.encode()
        ).hexdigest()


    # =====================================================
    # DICTIONARY
    # =====================================================

    def to_dict(self):

        return {

            "index": self.index,

            "timestamp": self.timestamp,

            "certificate_id": self.certificate_id,

            "certificate_hash": self.certificate_hash,

            "previous_hash": self.previous_hash,

            "hash": self.hash

        }


# =========================================================
# CERTIFICATE BLOCKCHAIN
# =========================================================

class CertificateBlockchain:

    def __init__(self):

        self.blockchain_file = os.path.join(

            os.path.dirname(__file__),

            "blockchain.json"

        )


        if os.path.exists(
            self.blockchain_file
        ):

            self.load_chain()

        else:

            self.chain = [
                self.create_genesis_block()
            ]

            self.save_chain()


    # =====================================================
    # GENESIS
    # =====================================================

    def create_genesis_block(self):

        return Block(

            0,

            str(datetime.now()),

            "GENESIS",

            "GENESIS",

            "0"

        )


    # =====================================================
    # LATEST BLOCK
    # =====================================================

    def get_latest_block(self):

        return self.chain[-1]


    # =====================================================
    # ADD CERTIFICATE
    # =====================================================

    def add_certificate(
        self,
        certificate_id,
        certificate_hash
    ):

        # Prevent duplicates

        if self.find_certificate(
            certificate_id
        ):

            return False


        previous_block = (
            self.get_latest_block()
        )


        new_block = Block(

            len(self.chain),

            str(datetime.now()),

            certificate_id,

            certificate_hash,

            previous_block.hash

        )


        self.chain.append(
            new_block
        )


        self.save_chain()


        return True


    # =====================================================
    # SAVE BLOCKCHAIN
    # =====================================================

    def save_chain(self):

        data = [

            block.to_dict()

            for block in self.chain

        ]


        with open(

            self.blockchain_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                data,

                file,

                indent=4

            )


    # =====================================================
    # LOAD BLOCKCHAIN
    # =====================================================

    def load_chain(self):

        try:

            with open(

                self.blockchain_file,

                "r",

                encoding="utf-8"

            ) as file:

                data = json.load(file)


            self.chain = []


            for item in data:

                block = Block(

                    item["index"],

                    item["timestamp"],

                    item["certificate_id"],

                    item["certificate_hash"],

                    item["previous_hash"]

                )


                block.hash = item["hash"]


                self.chain.append(block)


        except Exception:

            self.chain = [
                self.create_genesis_block()
            ]

            self.save_chain()


    # =====================================================
    # VERIFY BLOCKCHAIN
    # =====================================================

    def verify_chain(self):

        if not self.chain:

            return False


        for i in range(
            1,
            len(self.chain)
        ):

            current = self.chain[i]

            previous = self.chain[i - 1]


            if (
                current.hash
                != current.calculate_hash()
            ):

                return False


            if (
                current.previous_hash
                != previous.hash
            ):

                return False


        return True


    # =====================================================
    # FIND CERTIFICATE
    # =====================================================

    def find_certificate(
        self,
        certificate_id
    ):

        for block in self.chain:

            if (
                block.certificate_id
                == certificate_id
            ):

                return block


        return None


    # =====================================================
    # DICTIONARY
    # =====================================================

    def to_dict(self):

        return [

            block.to_dict()

            for block in self.chain

        ]