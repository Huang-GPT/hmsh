from app import db
from app.models.common_fault import CommonFault

class FaultService:
    
    @classmethod
    def create_fault(cls, product_model, fault_type, fault_desc, solution):
        fault = CommonFault(
            product_model=product_model,
            fault_type=fault_type,
            fault_desc=fault_desc,
            solution=solution
        )
        db.session.add(fault)
        db.session.commit()
        return fault
    
    @classmethod
    def get_faults_by_model(cls, product_model):
        return CommonFault.query.filter_by(product_model=product_model)\
            .order_by(CommonFault.view_count.desc()).all()
    
    @classmethod
    def search_faults(cls, product_model, keyword):
        return CommonFault.query.filter(
            CommonFault.product_model == product_model,
            db.or_(
                CommonFault.fault_type.like(f'%{keyword}%'),
                CommonFault.fault_desc.like(f'%{keyword}%'),
                CommonFault.solution.like(f'%{keyword}%')
            )
        ).all()
    
    @classmethod
    def get_fault_detail(cls, fault_id):
        fault = CommonFault.query.get(fault_id)
        if fault:
            fault.view_count += 1
            db.session.commit()
        return fault
    
    @classmethod
    def mark_helpful(cls, fault_id):
        fault = CommonFault.query.get(fault_id)
        if fault:
            fault.helpful_count += 1
            db.session.commit()
        return fault
    
    @classmethod
    def get_popular_faults(cls, limit=10):
        return CommonFault.query.order_by(CommonFault.view_count.desc())\
            .limit(limit).all()