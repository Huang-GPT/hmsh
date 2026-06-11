from flask import request, jsonify
from app.api import bp
from app.services.fault_service import FaultService

@bp.route('/faults', methods=['GET'])
def get_faults():
    product_model = request.args.get('product_model')
    keyword = request.args.get('keyword')
    
    if not product_model:
        return jsonify({'error': 'Missing product_model'}), 400
    
    if keyword:
        faults = FaultService.search_faults(product_model, keyword)
    else:
        faults = FaultService.get_faults_by_model(product_model)
    
    return jsonify({
        'faults': [fault.to_dict() for fault in faults]
    })

@bp.route('/faults/<int:fault_id>', methods=['GET'])
def get_fault_detail(fault_id):
    fault = FaultService.get_fault_detail(fault_id)
    if not fault:
        return jsonify({'error': 'Fault not found'}), 404
    return jsonify({'fault': fault.to_dict()})

@bp.route('/faults/<int:fault_id>/helpful', methods=['POST'])
def mark_helpful(fault_id):
    fault = FaultService.mark_helpful(fault_id)
    if not fault:
        return jsonify({'error': 'Fault not found'}), 404
    return jsonify({'message': 'Marked as helpful', 'fault': fault.to_dict()})

@bp.route('/faults/popular', methods=['GET'])
def get_popular_faults():
    limit = request.args.get('limit', 10, type=int)
    faults = FaultService.get_popular_faults(limit)
    return jsonify({
        'faults': [fault.to_dict() for fault in faults]
    })

@bp.route('/faults', methods=['POST'])
def create_fault():
    data = request.get_json()
    required_fields = ['product_model', 'fault_type', 'fault_desc', 'solution']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400
    
    fault = FaultService.create_fault(
        product_model=data['product_model'],
        fault_type=data['fault_type'],
        fault_desc=data['fault_desc'],
        solution=data['solution']
    )
    return jsonify({
        'message': 'Fault created',
        'fault': fault.to_dict()
    })