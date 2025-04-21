import json
from datetime import datetime
from collections import defaultdict
import os 
import pandas as pd
import numpy as np
import pycountry_convert as pc

def country_to_continent(country_name):
    """Convert country name to continent using pycountry-convert"""
    try:
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except:
        return "Unknown"

def generate_analytics(file_path):
    """Generate marketing analytics from CSV data"""
    # Load and clean data
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data', 'json', 'SocialMediaData.csv')
    df = pd.read_csv(file_path)
    df['Location'] = df['Location'].replace({'Barzil': 'Brazil'})
    
    # Generate analytics
    analytics = {}
    
    # 1. Demographic Analysis
    analytics['demographics'] = {
        'age_stats': df['Age'].describe().to_dict(),
        'gender_distribution': df['Gender'].value_counts().to_dict(),
        'income_stats': df['Income'].describe().to_dict()
    }
    
    # 2. Geographic Analysis (using pycountry-convert)
    df['Continent'] = df['Location'].apply(country_to_continent)
    analytics['geography'] = {
        'top_countries': df['Location'].value_counts().head(10).to_dict(),
        'continent_distribution': df['Continent'].value_counts().to_dict(),
        'income_by_continent': df.groupby('Continent')['Income'].mean().to_dict()
    }
    
    # 3. Professional Analysis  
    analytics['profession'] = {
        'common_professions': df['Profession'].value_counts().head(5).to_dict(),
        'income_by_profession': df.groupby('Profession')['Income'].mean().to_dict(),
        'debt_by_profession': df.groupby('Profession')['Debt'].mean().to_dict()
    }
    
    # 4. Behavioral Analysis
    analytics['behavior'] = {
        'platform_usage': df['Platform'].value_counts().to_dict(),
        'top_video_categories': df['Video Category'].value_counts().head(5).to_dict(),
        'engagement_stats': df['Engagement'].describe().to_dict()
    }
    
    # 5. Financial Analysis
    analytics['financial'] = {
        'debt_distribution': df['Debt'].value_counts(normalize=True).to_dict(),
        'property_ownership': df['Owns Property'].value_counts(normalize=True).to_dict(),
        'income_debt_correlation': df[['Income', 'Debt']].corr().iloc[0,1]
    }
    
    # 6. Advanced Metrics
    analytics['advanced'] = {
        'time_spent_vs_engagement': df[['Total Time Spent', 'Engagement']].corr().iloc[0,1],
        'device_usage': df['DeviceType'].value_counts().to_dict(),
        'top_engagement_times': df['Watch Time'].value_counts().head(5).to_dict()
    }
    
    return json.dumps(analytics, indent=4)

def load_json_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_csv_data(file_path):
    return pd.read_csv(file_path)

def analyze_transactions():
    # Initialize analysis containers
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

            # Spending by category
            primary_category = transaction['personal_finance_category']['primary']
            analysis['spending_by_category'][primary_category] += amount

            # Merchant analysis
            merchant = transaction['merchant_name'] or 'Unknown'
            analysis['spending_by_merchant'][merchant]['total'] += amount
            analysis['spending_by_merchant'][merchant]['count'] += 1

            # Monthly trends
            analysis['monthly_trends'][month_key] += amount

            # Account type analysis
            account_id = transaction['account_id']
            for user_account in user['accounts']['accounts']:
                if user_account['account_id'] == account_id:
                    acc_type = f"{user_account['type']} - {user_account['subtype']}"
                    analysis['account_type_analysis'][acc_type]['count'] += 1
                    analysis['account_type_analysis'][acc_type]['total'] += amount
                    break

            # Income vs expenses
            if transaction['amount'] > 0:
                analysis['income_vs_expenses']['income'] += amount
            else:
                analysis['income_vs_expenses']['expenses'] += amount

            # Cash flow analysis
            analysis['cash_flow'][transaction['date']] += transaction['amount']

            # Track top transactions
            analysis['top_transactions'].append({
                'date': transaction['date'],
                'merchant': merchant,
                'amount': amount,
                'category': primary_category
            })

    # Post-processing
    analysis['top_transactions'] = sorted(
        analysis['top_transactions'],
        key=lambda x: x['amount'],
        reverse=True
    )[:10]

    # Convert defaultdicts to regular dicts for JSON serialization
    analysis['spending_by_category'] = dict(analysis['spending_by_category'])
    analysis['spending_by_merchant'] = dict(analysis['spending_by_merchant'])
    analysis['monthly_trends'] = dict(analysis['monthly_trends'])
    analysis['account_type_analysis'] = dict(analysis['account_type_analysis'])
    analysis['cash_flow'] = dict(analysis['cash_flow'])

    return analysis

