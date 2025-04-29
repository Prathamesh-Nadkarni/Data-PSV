# Analytics.py

import os
import json
import joblib
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from threading import Thread
from datetime import datetime
from collections import defaultdict

import pycountry_convert as pc

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
import xgboost as xgb
import lightgbm as lgb

# Model storage
MODEL_DIR = "./models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ----------------------------------
# 1. Utility Functions for Analytics
# ----------------------------------

def load_json_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_csv_data(file_path):
    return pd.read_csv(file_path)

def country_to_continent(country_name):
    """Convert country name to continent using pycountry-convert."""
    try:
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except:
        return "Unknown"

# ----------------------------------
# 2. Social Media Data Analysis
# ----------------------------------

def generate_social_media_analytics():
    """Generate marketing analytics from social media data."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'csv', 'SocialMediaData.csv')
    df = pd.read_csv(file_path)
    df['Location'] = df['Location'].replace({'Barzil': 'Brazil'})
    df['Continent'] = df['Location'].apply(country_to_continent)

    analytics = {}

    analytics['demographics'] = {
        'age_stats': df['Age'].describe().to_dict(),
        'gender_distribution': df['Gender'].value_counts().to_dict(),
        'income_stats': df['Income'].describe().to_dict()
    }

    analytics['geography'] = {
        'top_countries': df['Location'].value_counts().head(10).to_dict(),
        'continent_distribution': df['Continent'].value_counts().to_dict(),
        'income_by_continent': df.groupby('Continent')['Income'].mean().to_dict()
    }

    analytics['profession'] = {
        'common_professions': df['Profession'].value_counts().head(5).to_dict(),
        'income_by_profession': df.groupby('Profession')['Income'].mean().to_dict(),
        'debt_by_profession': df.groupby('Profession')['Debt'].mean().to_dict()
    }

    analytics['behavior'] = {
        'platform_usage': df['Platform'].value_counts().to_dict(),
        'top_video_categories': df['Video Category'].value_counts().head(5).to_dict(),
        'engagement_stats': df['Engagement'].describe().to_dict()
    }

    analytics['financial'] = {
        'debt_distribution': df['Debt'].value_counts(normalize=True).to_dict(),
        'property_ownership': df['Owns Property'].value_counts(normalize=True).to_dict(),
        'income_debt_correlation': df[['Income', 'Debt']].corr().iloc[0, 1]
    }

    analytics['advanced'] = {
        'time_spent_vs_engagement': df[['Total Time Spent', 'Engagement']].corr().iloc[0, 1],
        'device_usage': df['DeviceType'].value_counts().to_dict(),
        'top_engagement_times': df['Watch Time'].value_counts().head(5).to_dict()
    }

    return json.dumps(analytics, indent=4)

def analyze_user_data_db():
    """Analyze user_data.db correctly based on accounts and transactions."""
    try:
        db_path = "../Data/sqllite-db/user_data.db" #os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'sqlite-db', 'user_data.db')
        conn = sqlite3.connect(db_path)

        analysis = {}

        # Analyze account types
        accounts_df = pd.read_sql_query("SELECT type, subtype FROM accounts", conn)
        analysis['account_types'] = accounts_df['type'].value_counts().to_dict()
        analysis['account_subtypes'] = accounts_df['subtype'].value_counts().to_dict()

        # Analyze transactions - Top Merchants
        transactions_df = pd.read_sql_query("SELECT merchant_name, amount, date, category FROM transactions", conn)
        analysis['top_merchants'] = transactions_df['merchant_name'].value_counts().head(10).to_dict()

        # Analyze transactions - Spending by Month
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        transactions_df['month'] = transactions_df['date'].dt.to_period('M')
        spending_by_month = transactions_df.groupby('month')['amount'].sum().sort_index()
        analysis['monthly_spending'] = {str(month): amount for month, amount in spending_by_month.items()}

        # Analyze transactions - Category Spending
        analysis['category_spending'] = transactions_df['category'].value_counts().head(10).to_dict()

        conn.close()
        return analysis

    except Exception as e:
        print(f"❌ Error analyzing user_data.db: {e}")
        return {}

def analyze_transactions():
    """Analyze user financial transactions."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'json', 'users_data.json')
    data = load_json_data(file_path)

    analysis = {
        'spending_by_category': defaultdict(float),
        'spending_by_merchant': defaultdict(lambda: {'total': 0.0, 'count': 0}),
        'monthly_trends': defaultdict(float),
        'account_type_analysis': defaultdict(lambda: {'count': 0, 'total': 0.0}),
        'income_vs_expenses': {'income': 0.0, 'expenses': 0.0},
        'cash_flow': defaultdict(float),
        'top_transactions': []
    }

    for user in data:
        for transaction in user.get('transactions', {}).get('transactions', []):
            amount = abs(transaction['amount'])
            date_obj = datetime.strptime(transaction['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')

            primary_category = transaction['personal_finance_category']['primary']
            merchant = transaction['merchant_name'] or 'Unknown'
            account_id = transaction['account_id']

            analysis['spending_by_category'][primary_category] += amount
            analysis['spending_by_merchant'][merchant]['total'] += amount
            analysis['spending_by_merchant'][merchant]['count'] += 1
            analysis['monthly_trends'][month_key] += amount

            for user_account in user['accounts']['accounts']:
                if user_account['account_id'] == account_id:
                    acc_type = f"{user_account['type']} - {user_account['subtype']}"
                    analysis['account_type_analysis'][acc_type]['count'] += 1
                    analysis['account_type_analysis'][acc_type]['total'] += amount
                    break

            if transaction['amount'] > 0:
                analysis['income_vs_expenses']['income'] += amount
            else:
                analysis['income_vs_expenses']['expenses'] += amount

            analysis['cash_flow'][transaction['date']] += transaction['amount']

            analysis['top_transactions'].append({
                'date': transaction['date'],
                'merchant': merchant,
                'amount': amount,
                'category': primary_category
            })

    analysis['top_transactions'] = sorted(
        analysis['top_transactions'],
        key=lambda x: x['amount'],
        reverse=True
    )[:10]

    analysis['spending_by_category'] = dict(analysis['spending_by_category'])
    analysis['spending_by_merchant'] = dict(analysis['spending_by_merchant'])
    analysis['monthly_trends'] = dict(analysis['monthly_trends'])
    analysis['account_type_analysis'] = dict(analysis['account_type_analysis'])
    analysis['cash_flow'] = dict(analysis['cash_flow'])

    return analysis

# ----------------------------------
# 3. ML Training Pipeline
# ----------------------------------

def load_data(db_connection):
    """Fetches data from SQLite."""
    query = "SELECT * FROM sales"
    df = pd.read_sql_query(query, db_connection)
    return df

def preprocess_data(df, target_column="quantity"):
    """Separate categorical and numerical preprocessing."""
    features = df.drop(columns=[target_column, 'id'])  # Drop 'id' if it's just identifier
    target = df[target_column]

    numeric_features = ['sales']  # numeric
    categorical_features = ['country', 'category', 'product_name']  # categorical

    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OrdinalEncoder())
    ])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

    features_processed = preprocessor.fit_transform(features)

    return features_processed, target, preprocessor

def train_random_forest(X, y):
    rf = RandomForestRegressor(random_state=42)
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 20],
        'min_samples_split': [2, 5, 10]
    }
    grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='neg_root_mean_squared_error', n_jobs=-1)
    grid_search.fit(X, y)

    joblib.dump(grid_search.best_estimator_, os.path.join(MODEL_DIR, "random_forest_model.pkl"))
    print(f"Best RF Params: {grid_search.best_params_}")

    return grid_search.best_estimator_

def train_xgboost(X, y):
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model.fit(X, y)
    joblib.dump(model, os.path.join(MODEL_DIR, "xgboost_model.pkl"))
    return model

def train_lightgbm(X, y):
    model = lgb.LGBMRegressor(objective='regression', random_state=42)
    model.fit(X, y)
    joblib.dump(model, os.path.join(MODEL_DIR, "lightgbm_model.pkl"))
    return model

def plot_feature_importance(model, feature_names, title):
    importances = model.feature_importances_
    indices = np.argsort(importances)

    plt.figure(figsize=(10, 6))
    plt.title(f"Feature Importances - {title}")
    plt.barh(range(len(indices)), importances[indices])
    plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, f"{title}_feature_importance.png"))
    plt.close()

def full_training_pipeline(db_connection):
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = load_data(conn)
    X, y, preprocessor = preprocess_data(df)

    rf_model = train_random_forest(X, y)
    xgb_model = train_xgboost(X, y)
    lgb_model = train_lightgbm(X, y)

    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessing_pipeline.pkl"))

    feature_names = df.drop(columns=['sales']).columns
    plot_feature_importance(rf_model, feature_names, "RandomForest")
    plot_feature_importance(xgb_model, feature_names, "XGBoost")
    plot_feature_importance(lgb_model, feature_names, "LightGBM")

    rf_cv_score = cross_val_score(rf_model, X, y, cv=5, scoring='neg_root_mean_squared_error')
    print(f"Random Forest CV RMSE: {-rf_cv_score.mean():.4f}")
    conn.close()
    return rf_model, xgb_model, lgb_model

def run_training_in_background(db_path):
    thread = Thread(target=full_training_pipeline, args=(db_path,))
    thread.start()
    return thread


if __name__ == "__main__":
    import sqlite3

    # Paths
    OUTPUT_DIR = "./analytics_output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("========== Starting Analytics Pipeline ==========")

    # 1. Generate Social Media Analytics
    print("\n[1/4] Running Social Media Analytics...")
    try:
        social_media_analytics = generate_social_media_analytics()
        with open(os.path.join(OUTPUT_DIR, "social_media_analytics.json"), "w") as f:
            f.write(social_media_analytics)
        print("✅ Social Media Analytics completed.")
    except Exception as e:
        print(f"❌ Error in Social Media Analytics: {e}")

    # 2. Analyze User Transactions
    print("\n[2/4] Running Transactions Analysis...")
    try:
        transactions_analysis = analyze_transactions()
        with open(os.path.join(OUTPUT_DIR, "transactions_analysis.json"), "w") as f:
            json.dump(transactions_analysis, f, indent=4)
        print("✅ Transactions Analysis completed.")
    except Exception as e:
        print(f"❌ Error in Transactions Analysis: {e}")

    # 2.5 Analyze user_data.db
    print("\n[2.5/4] Running user_data.db Analysis...")
    try:
        user_data_analysis = analyze_user_data_db()
        with open(os.path.join(OUTPUT_DIR, "user_data_analysis.json"), "w") as f:
            json.dump(user_data_analysis, f, indent=4)
        print("✅ user_data.db Analysis completed.")
    except Exception as e:
        print(f"❌ Error in user_data.db Analysis: {e}")


    # 3. Train ML Models
    print("\n[3/4] Starting Model Training...")
    try:
        # Connect to SQLite database
        db_path = "../Data/sqllite-db/sales_data.db" 
        #os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'sqlite-db', 'sales_data.db')
        # Run training in background
        training_thread = run_training_in_background(db_path)
        training_thread.join()  # Wait for training to finish

        print("✅ Model Training completed.")
    except Exception as e:
        print(f"❌ Error in Model Training: {e}")

    # 4. Final Summary
    print("\n[4/4] ✅ All tasks finished successfully. Analytics saved in:", OUTPUT_DIR)
    print("========== End of Analytics Pipeline ==========")
