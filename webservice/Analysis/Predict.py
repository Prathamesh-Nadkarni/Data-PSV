import torch
import torch.nn.functional as F
import pandas as pd
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv, Linear
import os

# Define the model architecture
class MarketingGNN(torch.nn.Module):
    def __init__(self, num_platforms):
        super().__init__()
        self.conv1 = HeteroConv({
            ('product', 'targets', 'demographic'): SAGEConv((32, 32), 64),
            ('demographic', 'rev_targets', 'product'): SAGEConv((32, 32), 64),
            ('demographic', 'uses', 'platform'): SAGEConv((32, 32), 64),
            ('platform', 'rev_uses', 'demographic'): SAGEConv((32, 32), 64),
            ('product', 'self', 'product'): SAGEConv((32, 32), 64),
        }, aggr='mean')
        self.lin = Linear(64, num_platforms)

    def forward(self, x_dict, edge_index_dict):
        x_dict = self.conv1(x_dict, edge_index_dict)
        x_dict = {key: F.leaky_relu(x) for key, x in x_dict.items()}
        return self.lin(x_dict['product'])

# Load model and maps
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'product_platform_gnn.pth')
checkpoint = torch.load(model_path)
product_map = checkpoint['product_map']
demo_map = checkpoint['demo_map']
platform_map = checkpoint['platform_map']
rev_platform_map = {v: k for k, v in platform_map.items()}

# Load product name to category mapping
csv_path = os.path.join(base_dir, '..', 'Data', 'csv', 'ProductData.csv')

# Load the CSV file
transactions = pd.read_csv(csv_path)
name_to_category = transactions.set_index('Product Name')['Product Category'].to_dict()

# Re-initialize model
model = MarketingGNN(num_platforms=len(platform_map))
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Dummy graph structure for inference
def create_dummy_graph(num_products):
    data = HeteroData()
    data['product'].x = torch.randn(num_products, 32)
    data['demographic'].x = torch.randn(len(demo_map), 32)
    data['platform'].x = torch.randn(len(platform_map), 32)
    data['product', 'self', 'product'].edge_index = torch.tensor(
        [[i, i] for i in range(num_products)], dtype=torch.long
    ).t().contiguous()
    return data

# Inference function
def predict_best_platform(product_name: str):
    if product_name not in name_to_category:
        raise ValueError(f"Unknown product name: {product_name}")
    
    product_category = name_to_category[product_name]
    if product_category not in product_map:
        raise ValueError(f"Product category '{product_category}' not found in model's product map.")

    product_idx = product_map[product_category]
    data = create_dummy_graph(len(product_map))

    with torch.no_grad():
        out = model(data.x_dict, data.edge_index_dict)
        pred_platform_idx = out[product_idx].argmax().item()
        return rev_platform_map[pred_platform_idx]



def  get_best_platform(product_name: str):
    """
    Given a product name, return the best platform to promote it.
    """
    try:
        best_platform = predict_best_platform(product_name)
        return best_platform
    except ValueError as e:
        print(e)
        return None
    