from flask import request, jsonify
from app.api import bp
from app.services.product_service import ProductService

@bp.route('/products/bind', methods=['POST'])
def bind_product():
    data = request.get_json()
    user_id = data.get('user_id')
    bind_method = data.get('bind_method')
    
    if not user_id or not bind_method:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        if bind_method == 'manual':
            product = ProductService.bind_product_manually(
                user_id=user_id,
                serial_number=data.get('serial_number'),
                model=data.get('model'),
                bind_method=bind_method
            )
        elif bind_method == 'order':
            product = ProductService.bind_product_by_order(
                user_id=user_id,
                sap_order_no=data.get('sap_order_no'),
                sap_line_item=data.get('sap_line_item')
            )
        else:
            return jsonify({'error': 'Invalid bind method'}), 400
        
        return jsonify({
            'message': 'Product bound successfully',
            'product': product.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/products', methods=['GET'])
def get_user_products():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    products = ProductService.get_user_products(user_id)
    return jsonify({'products': products})

@bp.route('/products/unbind', methods=['POST'])
def unbind_product():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    
    if not user_id or not product_id:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        ProductService.unbind_product(user_id, product_id)
        return jsonify({'message': 'Product unbound successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400