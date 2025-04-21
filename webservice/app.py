from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
)
from datetime import timedelta

from Analysis.Predict import predict_best_platform
from Analysis.ProductMedia import recommend_platforms
from Analysis.DataAnalytics import analyze_transactions
from DataSourcing.SQLliteCreate import createDB, authenticate_user, register_user, get_user_security_status
from DataSourcing.SQLRead import fetch_all_product_names, fetch_sales_by_product, fetch_sales_by_category

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)

app.config['JWT_SECRET_KEY'] = 'DATA-PSV-2025'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

jwt = JWTManager(app)
jwt_blacklist = set()
# ------------------ AUTH & USER MANAGEMENT ------------------
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in jwt_blacklist


@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Invalidate the current JWT by adding its jti to the blacklist.
    """
    jti = get_jwt()["jti"]
    jwt_blacklist.add(jti)
    return jsonify({"message": "Successfully logged out"}), 200

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        user_status = get_user_security_status(username)
        if not user_status:
            return jsonify({"error": "Invalid username or password"}), 401

        user_id = user_status[0]
        is_locked = user_status[4] == 1

        if is_locked:
            return jsonify({"error": "Account locked"}), 403

        role = authenticate_user(username, password)
        if role:
            access_token = create_access_token(
                identity=username,
                additional_claims={
                    "user_id": user_id,
                    "role": role
                }
            )
            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "role": role
            }), 200

        return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500

@app.route('/register', methods=['POST'])
def register():
    """
    Simulate a registration endpoint.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    try:
        register_user(username, password, role)
        return jsonify({"message": "Registration successful"}), 201
    except ValueError as ve:
        if str(ve) == "Username already exists":
            return jsonify({"error": "Username already exists"}), 409
        else:
            return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ PROTECTED API ENDPOINTS ------------------

@app.route('/get_best_platform', methods=['POST'])
#@jwt_required()
def get_best_platform():
    """
    Given a product name, return the best platform to promote it.
    """
    '''claims = get_jwt()
    if claims.get("role") != "company":
        return jsonify({"msg": "Company role required"}), 403
'''
    data = request.get_json()
    product_name = data.get('product_name')
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    try:
        best_platform = recommend_platforms(product_name)
        return jsonify({"best_platform": best_platform}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/get_products', methods=['GET'])
@jwt_required()
def get_products():
    """
    Fetch all products from the database.
    """
    claims = get_jwt()
    if claims.get("role") != "company":
        return jsonify({"msg": "Company role required"}), 403

    try:
        df = fetch_all_product_names()
        return jsonify(df.to_dict(orient='records')), 200
    except Exception as e:
        app.logger.error(f"Error fetching products: {str(e)}")
        return jsonify({"error": "Error fetching products"}), 500

@app.route('/analyze_transactions', methods=['GET'])
@jwt_required()
def analyze_transactions_endpoint():
    """
    Analyze transactions and return the results.
    """
    claims = get_jwt()
    if claims.get("role") != "company":
        return jsonify({"msg": "Company role required"}), 403

    try:
        analysis_results = analyze_transactions()
        return jsonify(analysis_results), 200
    except Exception as e:
        app.logger.error(f"Error analyzing transactions: {str(e)}")
        return jsonify({"error": "Error analyzing transactions"}), 500


@app.route('/user_security_status', methods=['GET'])
@jwt_required()
def user_security_status():
    """
    Fetch the security status of a user.
    """
    claims = get_jwt()
    if claims.get("role") != "user":
        return jsonify({"msg": "Company role required"}), 403

    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        user_status = get_user_security_status(username)
        if user_status:
            return jsonify({"user_status": user_status}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        app.logger.error(f"Error fetching user status: {str(e)}")
        return jsonify({"error": "Error fetching user status"}), 500

# ------------------ PUBLIC DATA ENDPOINTS ------------------

@app.route('/sales_by_product', methods=['GET'])
@jwt_required()
def sales_by_product():
    """
    Fetch sales data for a specific product.
    """
    product_name = request.args.get('product_name')

    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    try:
        df = fetch_sales_by_product(product_name)
        return jsonify(df.to_dict(orient='records')), 200
    except Exception as e:
        app.logger.error(f"Error fetching sales data: {str(e)}")
        return jsonify({"error": "Error fetching sales data"}), 500

@app.route('/sales_by_category', methods=['GET'])
@jwt_required()
def sales_by_category():
    """
    Fetch sales data for a specific product category.
    """
    product_category = request.args.get('product_category')

    if not product_category:
        return jsonify({"error": "Product category is required"}), 400

    try:
        df = fetch_sales_by_category(product_category)
        return jsonify(df.to_dict(orient='records')), 200
    except Exception as e:
        app.logger.error(f"Error fetching sales data: {str(e)}")
        return jsonify({"error": "Error fetching sales data"}), 500

# ------------------ APP INIT ------------------

if __name__ == "__main__":
    db_names = [
        'sales_data.db',
        'user_data.db',
        'social_media.db',
        'users_login.db'
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, '..', 'Data', 'sqllite-db')
    with app.app_context():
        for db_name in db_names:
            db_path = os.path.join(db_dir, db_name)
            if not os.path.exists(db_path):
                createDB(db_name)
                print(f"DB Created: {db_name}")
    app.run(host='0.0.0.0', port=5500, debug=True)
