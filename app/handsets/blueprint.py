from flask import Blueprint

from helpers import object_list
from models import Handset, DirNum

handsets = Blueprint('handsets', __name__, template_folder='templates')

@handsets.route('/')
def index():
    handsets = Handset.query.order_by(Handset.create_ts.desc())
    return object_list('handsets/index.html', handsets)

@handsets.route('/dirnum/')
def dirnums_index():
    pass

@handsets.route('/dirnum/<dn>/')
def dirnums_detail(dn):
    pass

@handsets.route('/<dn>/')
def detail(dn):
    pass

