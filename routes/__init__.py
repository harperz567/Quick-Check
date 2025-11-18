from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
patient_bp = Blueprint('patient', __name__, url_prefix='/api/patient')
visit_bp = Blueprint('visit', __name__, url_prefix='/api/visit')

# 导入路由
from routes import auth_routes, patient_routes, visit_routes