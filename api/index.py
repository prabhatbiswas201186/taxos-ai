import sys
sys.path.insert(0, 'backend/src')
from main import app
from mangum import Mangum

mangum_handler = Mangum(app)

def handler(request, context):
    return mangum_handler(request, context)
