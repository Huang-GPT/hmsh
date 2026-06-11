from flask import request, jsonify
from app.api import bp
from app.services.work_order_service import WorkOrderService

@bp.route('/work-orders', methods=['POST'])
def create_work_order():
    data = request.get_json()
    required_fields = ['user_id', 'product_id', 'fault_type', 'fault_desc', 
                       'contact_name', 'contact_phone']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400
    
    try:
        order = WorkOrderService.create_work_order(
            user_id=data['user_id'],
            product_id=data['product_id'],
            fault_type=data['fault_type'],
            fault_desc=data['fault_desc'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            images=data.get('images'),
            expected_time=data.get('expected_time')
        )
        return jsonify({
            'message': 'Work order created',
            'order': order.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/work-orders', methods=['GET'])
def get_user_orders():
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    orders = WorkOrderService.get_user_orders(user_id, status)
    return jsonify({
        'orders': [order.to_dict() for order in orders]
    })

@bp.route('/work-orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    try:
        detail = WorkOrderService.get_order_detail(order_id)
        return jsonify(detail)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/work-orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    operator_id = data.get('operator_id')
    remark = data.get('remark', '')
    
    if not new_status or not operator_id:
        return jsonify({'error': 'Missing status or operator_id'}), 400
    
    try:
        order = WorkOrderService.update_order_status(order_id, new_status, operator_id, remark)
        return jsonify({
            'message': 'Status updated',
            'order': order.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/work-orders/<int:order_id>/assign', methods=['POST'])
def assign_order(order_id):
    data = request.get_json()
    handler_id = data.get('handler_id')
    
    if not handler_id:
        return jsonify({'error': 'Missing handler_id'}), 400
    
    try:
        order = WorkOrderService.assign_order(order_id, handler_id)
        return jsonify({
            'message': 'Order assigned',
            'order': order.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400