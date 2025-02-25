import os
from transkribus_utils.transkribus_utils import ACDHTranskribusUtils

user = os.environ.get('TR_USER')
pw = os.environ.get('TR_PW')
ids = ['COL_ID', 'COL_ID2', 'COL_ID3']

for cid in ids:
    col_id = os.environ.get(cid)
    transkribus_client = ACDHTranskribusUtils(
        user=user,
        password=pw,
        transkribus_base_url="https://transkribus.eu/TrpServer/rest"
    )
    mpr_docs = transkribus_client.collection_to_mets(col_id, file_path='./mets')
