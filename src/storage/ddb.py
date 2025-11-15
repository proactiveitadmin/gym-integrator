import os
from ..common.aws import ddb_resource

class MessagesRepo:
    def __init__(self):
        self.table = ddb_resource().Table(os.environ.get("DDB_TABLE_MESSAGES", "Messages"))
    def put(self, item: dict): self.table.put_item(Item=item)

class ConversationsRepo:
    def __init__(self):
        self.table = ddb_resource().Table(os.environ.get("DDB_TABLE_CONVERSATIONS", "Conversations"))
    def get(self, pk: str): return self.table.get_item(Key={"pk": pk}).get("Item")
    def put(self, item: dict): self.table.put_item(Item=item)
    def delete(self, pk: str): self.table.delete_item(Key={"pk": pk})
