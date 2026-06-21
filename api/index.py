import sys
sys.path.insert(0, 'backend/src')
from main import app as fastapi_app
from mangum import Mangum

app = Mangum(fastapi_app)
