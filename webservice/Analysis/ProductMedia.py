import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv, Linear

# Load and preprocess data
transactions = pd.read_csv('../Data/csv/Product Data.csv')
user_data = pd.read_csv('../Data/csv/Social Media Data.csv')

# Step 1: Analyze product trends
product_trends = transactions.groupby('Product Category').agg({
    'Units Sold': 'sum',
    'Total Revenue': 'sum'
}).reset_index()

# Step 2: Demographic analysis
user_data['AgeGroup'] = pd.cut(user_data['Age'], bins=[0, 18, 25, 35, 50, 100],
                              labels=['<18', '18-24', '25-34', '35-49', '50+'])
user_data['Demographic'] = user_data['AgeGroup'].astype(str) + "_" + user_data['Location']

# Step 3: Platform preference
platform_preference = user_data.groupby(['Demographic', 'Platform']).size().reset_index(name='Count')

# Create mappings
product_categories = product_trends['Product Category'].unique()
demographics = user_data['Demographic'].unique()
platforms = user_data['Platform'].unique()

product_map = {cat: idx for idx, cat in enumerate(product_categories)}
demo_map = {demo: idx for idx, demo in enumerate(demographics)}
platform_map = {plat: idx for idx, plat in enumerate(platforms)}

# Build heterogeneous graph
data = HeteroData()

# Node features
data['product'].x = torch.randn(len(product_categories), 32)
data['demographic'].x = torch.randn(len(demographics), 32)
data['platform'].x = torch.randn(len(platforms), 32)

# Create edges with dimensional validation
def create_edges(edge_list, default_shape=(2, 0)):
    if len(edge_list) == 0:
        return torch.empty(default_shape, dtype=torch.long)
    tensor = torch.tensor(edge_list, dtype=torch.long).t()
    return tensor.contiguous() if tensor.dim() == 2 else tensor.view(2, -1)

# Product-Demographic edges
product_demo_edges = []
for _, row in user_data.iterrows():
    if row['Video Category'] in product_map and row['Demographic'] in demo_map:
        product_idx = product_map[row['Video Category']]
        demo_idx = demo_map[row['Demographic']]
        product_demo_edges.append([product_idx, demo_idx])
data['product', 'targets', 'demographic'].edge_index = create_edges(product_demo_edges)

# Demographic-Platform edges
demo_platform_edges = []
for _, row in platform_preference.iterrows():
    if row['Demographic'] in demo_map and row['Platform'] in platform_map:
        demo_idx = demo_map[row['Demographic']]
        plat_idx = platform_map[row['Platform']]
        demo_platform_edges.append([demo_idx, plat_idx])
data['demographic', 'uses', 'platform'].edge_index = create_edges(demo_platform_edges)

# Self-loop edges for products
self_edges = [[i, i] for i in range(len(product_categories))]
data['product', 'self', 'product'].edge_index = create_edges(self_edges)

# Heterogeneous GNN Model
class MarketingGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = HeteroConv({
            ('product', 'targets', 'demographic'): SAGEConv((32, 32), 64),
            ('demographic', 'rev_targets', 'product'): SAGEConv((32, 32), 64),
            ('demographic', 'uses', 'platform'): SAGEConv((32, 32), 64),
            ('platform', 'rev_uses', 'demographic'): SAGEConv((32, 32), 64),
            ('product', 'self', 'product'): SAGEConv((32, 32), 64),
        }, aggr='mean')
        
        self.lin = Linear(64, len(platforms))

    def forward(self, x_dict, edge_index_dict):
        x_dict = self.conv1(x_dict, edge_index_dict)
        x_dict = {key: F.leaky_relu(x) for key, x in x_dict.items()}
        return self.lin(x_dict['product'])

# Initialize and train
model = MarketingGNN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(100):
    model.train()
    out = model(data.x_dict, data.edge_index_dict)
    
    # Create targets with error handling
    try:
        merged = pd.merge(
            user_data[['Video Category']],
            transactions[['Product Category']],
            left_on='Video Category',
            right_on='Product Category',
            how='inner'
        )
        product_platform_counts = merged.groupby(['Product Category', 'Platform']).size()
        target_platforms = product_platform_counts.groupby('Product Category').idxmax().map(
            lambda x: platform_map.get(x[1], 0)
        ).reindex(product_categories, fill_value=0)
    except KeyError:
        target_platforms = pd.Series([0]*len(product_categories), index=product_categories)
    
    loss = F.cross_entropy(out, torch.tensor(target_platforms.values, dtype=torch.long))
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    print(f'Epoch {epoch+1}, Loss: {loss.item():.4f}')

# Save model
torch.save({
    'model_state_dict': model.state_dict(),
    'product_map': product_map,
    'demo_map': demo_map,
    'platform_map': platform_map
}, 'product_platform_gnn.pth')

print("Model successfully trained and saved!")
