from flask import request, jsonify, g
from sqlalchemy.orm import joinedload
from app.api import bp
from app.services.auth_service import login_required, role_required, hash_password
from app.models.user import User
from app.models.service_point import ServicePoint, Engineer
from app.models.work_order import WorkOrder
from app.models.common_fault import FaultCategory, CommonFault
from app.models.product import Product
from app.models.system import SystemConfig, LegacyRolePermission
from app import db
import csv
import io
from datetime import datetime
