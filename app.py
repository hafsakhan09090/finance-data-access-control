from flask import Flask, request, jsonify
from models import db, User, Transaction
from auth import generate_token, token_required, roles_required
from datetime import datetime, date
from sqlalchemy import func, extract

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

db.init_app(app)

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if user.status != 'active':
        return jsonify({'error': 'Account is inactive'}), 401
    
    token = generate_token(user.id, user.role)
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })

# ==================== USER ROUTES ====================

@app.route('/api/users', methods=['GET'])
@roles_required('admin')
def get_users():
    """Get all users (Admin only)"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users', methods=['POST'])
@roles_required('admin')
def create_user():
    """Create new user (Admin only)"""
    data = request.json
    
    # Validation
    required_fields = ['username', 'password', 'email']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        password=data['password'],  # In production, hash this!
        email=data['email'],
        role=data.get('role', 'viewer'),
        status=data.get('status', 'active')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@roles_required('admin')
def update_user(user_id):
    """Update user (Admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    if 'role' in data:
        user.role = data['role']
    if 'status' in data:
        user.status = data['status']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@roles_required('admin')
def delete_user(user_id):
    """Delete user (Admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

# ==================== TRANSACTION ROUTES ====================

@app.route('/api/transactions', methods=['GET'])
@token_required
def get_transactions():
    """Get transactions with filtering"""
    query = Transaction.query.filter_by(user_id=request.current_user.id)
    
    # Filter by type
    tx_type = request.args.get('type')
    if tx_type and tx_type in ['income', 'expense']:
        query = query.filter_by(type=tx_type)
    
    # Filter by category
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    # Filter by date
    date_str = request.args.get('date')
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    transactions = query.order_by(Transaction.date.desc()).all()
    return jsonify([tx.to_dict() for tx in transactions])

@app.route('/api/transactions', methods=['POST'])
@roles_required('admin', 'analyst')
def create_transaction():
    """Create new transaction"""
    data = request.json
    
    # Validation
    required_fields = ['amount', 'type', 'category', 'date']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        return jsonify({'error': 'Amount must be a positive number'}), 400
    
    try:
        tx_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    transaction = Transaction(
        amount=data['amount'],
        type=data['type'],
        category=data['category'],
        date=tx_date,
        notes=data.get('notes', ''),
        user_id=request.current_user.id
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(transaction.to_dict()), 201

@app.route('/api/transactions/<int:tx_id>', methods=['PUT'])
@roles_required('admin', 'analyst')
def update_transaction(tx_id):
    """Update transaction"""
    transaction = Transaction.query.get(tx_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    # Check if user owns this transaction or is admin
    if transaction.user_id != request.current_user.id and request.current_user_role != 'admin':
        return jsonify({'error': 'You can only update your own transactions'}), 403
    
    data = request.json
    
    if 'amount' in data:
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            return jsonify({'error': 'Amount must be a positive number'}), 400
        transaction.amount = data['amount']
    
    if 'type' in data:
        if data['type'] not in ['income', 'expense']:
            return jsonify({'error': 'Type must be income or expense'}), 400
        transaction.type = data['type']
    
    if 'category' in data:
        transaction.category = data['category']
    
    if 'date' in data:
        try:
            transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if 'notes' in data:
        transaction.notes = data['notes']
    
    db.session.commit()
    return jsonify(transaction.to_dict())

@app.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
@roles_required('admin')
def delete_transaction(tx_id):
    """Delete transaction (Admin only)"""
    transaction = Transaction.query.get(tx_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted successfully'})

# ==================== DASHBOARD ROUTES ====================

@app.route('/api/dashboard/summary', methods=['GET'])
@token_required
def get_summary():
    """Get income, expense, and net balance totals"""
    
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == request.current_user.id,
        Transaction.type == 'income'
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == request.current_user.id,
        Transaction.type == 'expense'
    ).scalar() or 0
    
    net_balance = total_income - total_expense
    
    return jsonify({
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'net_balance': float(net_balance)
    })

@app.route('/api/dashboard/trends', methods=['GET'])
@token_required
def get_trends():
    """Get monthly income/expense trends"""
    
    # Get current year or specified year
    year = request.args.get('year', datetime.now().year, type=int)
    
    monthly_data = []
    for month in range(1, 13):
        income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == request.current_user.id,
            Transaction.type == 'income',
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar() or 0
        
        expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == request.current_user.id,
            Transaction.type == 'expense',
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        ).scalar() or 0
        
        monthly_data.append({
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'income': float(income),
            'expense': float(expense)
        })
    
    return jsonify(monthly_data)

@app.route('/api/dashboard/categories', methods=['GET'])
@token_required
def get_category_breakdown():
    """Get category-wise totals for expenses"""
    
    categories = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == request.current_user.id,
        Transaction.type == 'expense'
    ).group_by(Transaction.category).all()
    
    result = [{'category': cat, 'total': float(total)} for cat, total in categories]
    
    return jsonify(result)

@app.route('/api/dashboard/recent', methods=['GET'])
@token_required
def get_recent_activity():
    """Get recent 10 transactions"""
    
    limit = request.args.get('limit', 10, type=int)
    recent = Transaction.query.filter_by(
        user_id=request.current_user.id
    ).order_by(Transaction.date.desc()).limit(limit).all()
    
    return jsonify([tx.to_dict() for tx in recent])

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Finance API is running'})

# ==================== INITIALIZE DATABASE ====================

def init_db():
    """Create tables and seed initial data"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create default users
        default_users = [
            {'username': 'admin', 'password': 'admin123', 'email': 'admin@example.com', 'role': 'admin', 'status': 'active'},
            {'username': 'analyst1', 'password': 'analyst123', 'email': 'analyst@example.com', 'role': 'analyst', 'status': 'active'},
            {'username': 'viewer1', 'password': 'viewer123', 'email': 'viewer@example.com', 'role': 'viewer', 'status': 'active'},
        ]
        
        for user_data in default_users:
            user = User(**user_data)
            db.session.add(user)
        
        db.session.commit()
        
        # Seed some sample transactions for admin
        admin = User.query.filter_by(username='admin').first()
        
        sample_transactions = [
            {'amount': 5000, 'type': 'income', 'category': 'Salary', 'date': date(2026, 3, 1), 'notes': 'March salary', 'user_id': admin.id},
            {'amount': 200, 'type': 'expense', 'category': 'Food', 'date': date(2026, 3, 2), 'notes': 'Groceries', 'user_id': admin.id},
            {'amount': 100, 'type': 'expense', 'category': 'Transport', 'date': date(2026, 3, 3), 'notes': 'Uber ride', 'user_id': admin.id},
            {'amount': 500, 'type': 'expense', 'category': 'Shopping', 'date': date(2026, 3, 5), 'notes': 'Clothes', 'user_id': admin.id},
            {'amount': 1000, 'type': 'income', 'category': 'Freelance', 'date': date(2026, 3, 10), 'notes': 'Web project', 'user_id': admin.id},
            {'amount': 300, 'type': 'expense', 'category': 'Entertainment', 'date': date(2026, 3, 12), 'notes': 'Movie night', 'user_id': admin.id},
            {'amount': 150, 'type': 'expense', 'category': 'Food', 'date': date(2026, 3, 15), 'notes': 'Restaurant', 'user_id': admin.id},
        ]
        
        for tx_data in sample_transactions:
            transaction = Transaction(**tx_data)
            db.session.add(transaction)
        
        db.session.commit()
        print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
