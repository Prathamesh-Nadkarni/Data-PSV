from plaid.api import plaid_api
from plaid import Configuration, ApiClient
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.sandbox_item_fire_webhook_request import SandboxItemFireWebhookRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.webhook_type import WebhookType
import time
from datetime import date

import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO 8601 string format
        return super().default(obj)


# Plaid API Configuration
configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        'clientId': '67d8b031b5155d00241372fd',
        'secret': '3f085ffe59f574eb84790ac935e1e1',
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# List of users
users = [
    {"user_id": "user_0", "client_user_id": "unique-id-0"},
    {"user_id": "user_1", "client_user_id": "unique-id-1"},
    {"user_id": "user_2", "client_user_id": "unique-id-2"},
    {"user_id": "user_3", "client_user_id": "unique-id-3"},
    {"user_id": "user_4", "client_user_id": "unique-id-4"},
    {"user_id": "user_5", "client_user_id": "unique-id-5"},
    {"user_id": "user_6", "client_user_id": "unique-id-6"},
    {"user_id": "user_7", "client_user_id": "unique-id-7"},
    {"user_id": "user_8", "client_user_id": "unique-id-8"},
    {"user_id": "user_9", "client_user_id": "unique-id-9"}
]

# Function to create link token for a user
def create_link_token(client_user_id):
    request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name='Your App Name',
        country_codes=[CountryCode('US')],
        language='en',
        user={'client_user_id': client_user_id}
    )
    response = client.link_token_create(request)
    return response.to_dict()['link_token']

# Public token exchange for access token
def exchange_public_token(public_token):
    exchange_response = client.item_public_token_exchange({'public_token': public_token})
    return exchange_response.to_dict()['access_token']

# Simulating transactions in the sandbox
def simulate_transactions(access_token):
    fire_webhook_request = SandboxItemFireWebhookRequest(
        access_token=access_token,
        webhook_code="DEFAULT_UPDATE",
        webhook_type=WebhookType("TRANSACTIONS")  # Use WebhookType enum
    )
    client.sandbox_item_fire_webhook(fire_webhook_request)
    print("Test transactions simulated for access token:", access_token)

# Fetching accounts
def fetch_accounts(access_token):
    accounts_response = client.accounts_get({'access_token': access_token})
    return accounts_response.to_dict()

# Fetch all transactions for a user
def fetch_transactions(access_token):
    all_transactions = []
    cursor = ""  # Start with an empty cursor
    
    while True:
        transactions_request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=cursor,
            count=500  # Maximum allowed per request
        )
        transactions_response = client.transactions_sync(transactions_request)
        data = transactions_response.to_dict()
        
        all_transactions.extend(data['added'])
        cursor = data['next_cursor']
        
        if not data['has_more']:
            break
    
    return {
        'transactions': all_transactions,
        'latest_cursor': cursor
    }

# Create users, simulate transactions, and fetch data
all_users_data = []

for user in users:
    print(f"Processing {user['user_id']}...")
    
    link_token = create_link_token(user["client_user_id"])
    
    sandbox_request = SandboxPublicTokenCreateRequest(
    institution_id='ins_109508',  # "First Platypus Bank"
    initial_products=[Products("transactions")],
        options={
            "webhook": "https://webhook.example.com"
        }
    )
    sandbox_response = client.sandbox_public_token_create(sandbox_request)
    public_token = sandbox_response.to_dict()['public_token']
    
    access_token = exchange_public_token(public_token)
    
    simulate_transactions(access_token)
    time.sleep(5)
    
    accounts_data = fetch_accounts(access_token)
    transactions_data = fetch_transactions(access_token)
    
    user_data = {
        "user_id": user["user_id"],
        "accounts": accounts_data,
        "transactions": transactions_data,
    }
    
    all_users_data.append(user_data)

# Saving all users' data to JSON file
with open("../Data/json/users_data.json", "w") as json_file:
    json.dump(all_users_data, json_file, indent=4, cls=CustomJSONEncoder)

print("All users' data saved to 'users_data.json'")
