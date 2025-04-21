import pandas as pd
import random
# Load Online-Sales-Data.csv (columns: Region, Product Category, Product Name, Total Revenue, Units Sold)
sales_data = pd.read_csv('..\Data\csv\Products.csv')

# Load Sample-Superstore.csv with encoding to handle special characters
superstore_data = pd.read_csv('..\Data\csv\Superstore.csv', encoding='latin1')
# Define comprehensive continent-country mapping
continent_countries = {
    'North America': ['United States', 'Canada', 'Mexico'],
    'Europe': ['Germany', 'France', 'Italy', 'Spain', 'UK'],
    'Asia': ['Japan', 'China', 'India', 'South Korea', 'Singapore'],
    'South America': ['Brazil', 'Argentina', 'Chile'],
    'Africa': ['South Africa', 'Egypt', 'Nigeria'],
    'Oceania': ['Australia', 'New Zealand']
}

# Process sales data (replace continents with countries)
sales_clean = sales_data[['Region', 'Product Category', 'Product Name', 'Total Revenue', 'Units Sold']]
sales_clean.columns = ['Country', 'Category', 'Product Name', 'Sales', 'Quantity']

def replace_continent_with_country(continent):
    return random.choice(continent_countries.get(continent, [continent]))

sales_clean['Country'] = sales_clean['Country'].apply(replace_continent_with_country)

# Process superstore data (replace US with global countries)
superstore_clean = superstore_data[['Country', 'Category', 'Product Name', 'Sales', 'Quantity']]

# Get all possible countries from mapping
all_countries = [country for sublist in continent_countries.values() for country in sublist]
used_countries = set(sales_clean['Country'].unique())
available_countries = [c for c in all_countries if c not in used_countries][:22-len(used_countries)]

def replace_us_with_country(country):
    return random.choice(available_countries) if country == 'United States' else country

superstore_clean['Country'] = superstore_clean['Country'].apply(replace_us_with_country)

# Combine datasets
combined_data = pd.concat([sales_clean, superstore_clean], ignore_index=True)

# Ensure total unique countries <= 22
combined_data = combined_data[combined_data['Country'].isin(list(used_countries) + available_countries)]

# Save to CSV
combined_data.to_csv('combined_dataset.csv', index=False)