from datetime import datetime
from app import db
from app.models.product import Product, UserProduct
from app.models.user import User

class ProductService:
    
    @classmethod
    def bind_product_manually(cls, user_id, serial_number, model, bind_method='manual'):
        product = Product.query.filter_by(serial_number=serial_number).first()
        if not product:
            product = Product(
                serial_number=serial_number,
                model=model,
                status='active'
            )
            db.session.add(product)
            db.session.commit()
        
        existing_bind = UserProduct.query.filter_by(
            user_id=user_id,
            product_id=product.id
        ).first()
        if existing_bind:
            raise ValueError('Product already bound to this user')
        
        user_product = UserProduct(
            user_id=user_id,
            product_id=product.id,
            bind_method=bind_method
        )
        db.session.add(user_product)
        db.session.commit()
        
        return product
    
    @classmethod
    def bind_product_by_order(cls, user_id, sap_order_no, sap_line_item):
        product = Product.query.filter_by(
            sap_order_no=sap_order_no,
            sap_line_item=sap_line_item
        ).first()
        
        if not product:
            raise ValueError('Product not found for given order')
        
        existing_bind = UserProduct.query.filter_by(product_id=product.id).first()
        if existing_bind:
            raise ValueError('Product already bound to another user')
        
        user_product = UserProduct(
            user_id=user_id,
            product_id=product.id,
            bind_method='order'
        )
        db.session.add(user_product)
        db.session.commit()
        
        return product
    
    @classmethod
    def get_user_products(cls, user_id):
        user_products = UserProduct.query.filter_by(user_id=user_id).all()
        products = []
        for up in user_products:
            product = Product.query.get(up.product_id)
            if product:
                products.append({
                    **product.to_dict(),
                    'bind_time': up.bind_time.isoformat(),
                    'bind_method': up.bind_method
                })
        return products
    
    @classmethod
    def unbind_product(cls, user_id, product_id):
        user_product = UserProduct.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
        
        if not user_product:
            raise ValueError('Product not bound to this user')
        
        db.session.delete(user_product)
        db.session.commit()
        return True