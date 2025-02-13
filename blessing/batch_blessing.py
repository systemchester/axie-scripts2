import requests
import json
import os
import time
from web3 import Web3
import threading


### ============方法定义 start =============
# 开始祈福
def start(private_key):
    # 合约地址: https://app.roninchain.com/address/ronin:9d3936dbd9a794ee31ef9f13814233d435bd806c
    blessing_contract_address='0x9d3936dbd9a794ee31ef9f13814233d435bd806c'
    ronin_rpc = 'https://api.roninchain.com/rpc'
    provider = Web3.HTTPProvider(ronin_rpc)
    w3 = Web3(provider)

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blessing_abi.json'), 'r') as file:
        abi = json.load(file)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(blessing_contract_address), 
        abi=abi
    )

    signer = w3.eth.account.from_key(private_key)
    address = signer.address
    current = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    if has_currently_activated(contract, address):
        print(f'[{current}] {address} 已祈福')
        return
    if activate_streak(w3, contract, signer):
        print(f'[{current}] {address} 祈福成功')
        return

# 检查当前账号是否已经祈福（不会消耗gas费）
def has_currently_activated(contract, address):
    return contract.functions.hasCurrentlyActivated(address).call()

# 向区块发送祈福请求（执行会消耗gas费）
def activate_streak(w3, contract, signer):
    try:
        transaction = contract.functions.activateStreak().build_transaction({
            'chainId': 2020,
            'nonce': w3.eth.get_transaction_count(signer.address),
            'gasPrice': w3.to_wei('20', 'gwei')
        })
        signed_txn = signer.sign_transaction(transaction)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return True
    except Exception as e:
        print(f'祈福失败 {signer.address} - {e}')
        return False
### ============方法定义 end =============

### ============脚本执行 start =============
# 从.blessing_keys文件中读取想要祈福的账号
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_batch_blessing_env'), 'r') as file:
  # 使用 json.load() 方法加载数据
  keys = json.load(file)

# 遍历所有账号，挨个祈福
# for key in keys:
#   start(key)


# 多线程遍历所有账号，挨个祈福
def process_keys(keys):
    for key in keys:
        start(key)
        
# 计算每个线程要处理的 keys 列表 max_threads为最大线程数量
max_threads = 5
keys_per_thread = len(keys) // max_threads
thread_list = []

# 创建并启动线程
for i in range(max_threads):
    start_index = i * keys_per_thread
    end_index = start_index + keys_per_thread if i < max_threads - 1 else len(keys)
    thread_keys = keys[start_index:end_index]
    thread = threading.Thread(target=process_keys, args=(thread_keys,))
    thread_list.append(thread)
    thread.start()
    print(i)

# 等待所有线程完成
for thread in thread_list:
    thread.join()
print("All blessing have finished.")

### ============脚本执行 end =============
