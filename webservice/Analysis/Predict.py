import torch
import torch.nn.functional as F
import pandas as pd
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv, Linear
import os
import pycountry_convert as pc

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

def country_to_continent(country_name):
    """Convert country name to continent using pycountry-convert"""
    try:
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except:
        return "Unknown"

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
name_to_category = transactions.set_index('Product Name')['Category'].to_dict()

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
        logits = out[product_idx]
        
        # Calculate probabilities using softmax
        probabilities = F.softmax(logits, dim=0)
        percentages = probabilities * 100
        
        # Create platform percentage mapping
        platform_percentages = {
            rev_platform_map[i]: round(percent.item(), 2)
            for i, percent in enumerate(percentages)
        }
        
        best_platform_idx = logits.argmax().item()
        
    return {
        'best_platform': rev_platform_map[best_platform_idx],
        'platform_percentages': platform_percentages
    }


def get_best_platform(product_name: str):
    """
    Given a product name, return the best platform to promote it.
    """
    try:
        return predict_best_platform(product_name)
    except ValueError as e:
        print(e)
        return None
