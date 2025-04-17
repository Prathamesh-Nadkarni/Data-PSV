from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt


from Analysis.Predict import predict_best_platform
from DataSourcing.SQLliteCreate import createDB, authenticate_user, register_user, get_user_security_status
from DataSourcing.SQLliteRead import fetch_sales_by_product

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['JWT_SECRET_KEY'] = 'DATA-PSV-2025' 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600*24

jwt = JWTManager(app)

@app.route('/get_best_platform', methods=['GET'])
@jwt_required()
def get_best_platform():
    """
    Given a product name, return the best platform to promote it.
    """
    claims = get_jwt()
    if claims.get("role") != "company":
        return {"msg": "Company role required"}, 403
    else: 
        data = request.get_json()
        product_name = data.get('product_name')
        
        if not product_name:
            return jsonify({"error": "Product name is required"}), 400
    
        try:
            best_platform = predict_best_platform(product_name)
            return jsonify({"best_platform": best_platform}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    


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
        
        # Check if account is locked
        if user_status and user_status[4] == 1:
            return jsonify({"error": "Account locked"}), 403
            
        if authenticate_user(username, password):
            # Create JWT with additional claims
            access_token = create_access_token(
                identity=username,
                additional_claims={
                    "user_id": user_status[0],
                    "role": "user"
                }
            )
            return jsonify({
                "message": "Login successful",
                "access_token": access_token
            }), 200
            
        return jsonify({"error": "Invalid credentials"}), 401
        
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
    
    if register_user(username, password):
        return jsonify({"message": "Registration successful"}), 201
    else:
        return jsonify({"error": "Invalid data"}), 400


@app.route('/sales_by_product', methods=['GET'])
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
    

if __name__ == "__main__":

    db_names = [
        'sales_data.db',
        'user_data.db',
        'social_media.db',
        'users_login.db'
    ]
    with app.app_context():
        for db_name in db_names:
            if not os.path.exists(db_name):
                createDB(db_name)
                print("DB Created")
    app.run(host='0.0.0.0', port=5500, debug=True)