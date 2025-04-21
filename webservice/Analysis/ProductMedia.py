import pandas as pd
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import os

# Load datasets
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'csv', 'SocialMediaData.csv')
social_media = pd.read_csv(file_path)
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'csv', 'ProductData.csv')
product_data = pd.read_csv(file_path)
social_media = social_media.rename(columns={'Location': 'Country'})

# Define features explicitly
numeric_features = ['Engagement', 'Time Spent On Video', 'Scroll Rate', 
                    'ProductivityLoss', 'Addiction Level']
categorical_features = ['Platform', 'Category', 'Video Category']

# Create preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), categorical_features)
    ],
    remainder='drop'
)

# Create full pipeline
model = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# Prepare training data
merged_data = pd.merge(social_media, product_data, on='Country')
X_train = merged_data[numeric_features + categorical_features]
y_train = merged_data['Sales']

# Train model
model.fit(X_train, y_train)

def recommend_platforms(product_name):
    # Validate product data structure
    required_product_columns = {'Product Name', 'Category', 'Sales'}
    if not required_product_columns.issubset(product_data.columns):
        missing = required_product_columns - set(product_data.columns)
        raise ValueError(f"Missing columns in product data: {missing}")

    # Check if product exists
    product_match = product_data[product_data['Product Name'] == product_name]
    if product_match.empty:
        raise ValueError(f"Product '{product_name}' not found in dataset")
    product_category = product_match['Category'].values[0]

    # Validate social media data structure
    required_social_columns = {'Country', 'Platform', 'Engagement', 
                              'Time Spent On Video', 'Scroll Rate',
                              'ProductivityLoss', 'Addiction Level'}
    if not required_social_columns.issubset(social_media.columns):
        missing = required_social_columns - set(social_media.columns)
        raise ValueError(f"Missing columns in social media data: {missing}")

    recommendations = {}
    
    for country in social_media['Country'].unique():
        country_data = social_media[social_media['Country'] == country]
        platform_scores = {}

        for platform in country_data['Platform'].unique():
            try:
                # Get only numeric features explicitly
                platform_features = country_data[
                    (country_data['Platform'] == platform)
                ][numeric_features].mean(numeric_only=True)
                
                # Handle potential NaN values from mean calculation
                if platform_features.isna().any():
                    print(f"Skipping {platform} in {country} due to missing data")
                    continue

                # Get most common video category
                video_category = country_data['Video Category'].mode()[0] if not country_data['Video Category'].empty else 'Unknown'

                # Create input data with explicit column order
                input_data = pd.DataFrame([{
                    **platform_features.to_dict(),
                    'Platform': platform,
                    'Category': product_category,
                    'Video Category': video_category
                }], columns=numeric_features + categorical_features)

                predicted_sales = model.predict(input_data)[0]
                platform_scores[platform] = predicted_sales
                
            except Exception as e:
                print(f"Skipping {platform} in {country}: {str(e)}")
                continue

        if platform_scores:
            total = sum(platform_scores.values())
            recommendations[country] = {
                platform: round((score/total)*100, 2)
                for platform, score in platform_scores.items()
            }

    return json.dumps(recommendations, indent=2)

