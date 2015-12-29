import datetime, re
from app import db

handset_dirnums = db.Table('handset_dirnums', 
        db.Column('hs_id', db.Integer, db.ForeignKey('handset.id')),  
        db.Column('dn_id', db.Integer, db.ForeignKey('dir_num.id'))
        )

class Handset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ephone_id = db.Column(db.Integer, unique=True)
    desc = db.Column(db.String(100))
    mac_addr = db.Column(db.String(14), unique=True)
    ephone_templ = db.Column(db.Integer, default=1)
    ephone_type = db.Column(db.Integer, default=7911)
    button = db.Column(db.Integer)
    cred_user = db.Column(db.String(24))
    cred_pass = db.Column(db.String(24))
    cfg_pickle = db.Column(db.Text)
    last_update_by = db.Column(db.String(10), default="System")
    create_ts = db.Column(db.DateTime, default=datetime.datetime.now)
    update_ts = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    dirnum = db.relationship('DirNum', secondary=handset_dirnums, backref=db.backref('dirnums', lazy='dynamic'))
    
    def __init__(self, *args, **kwargs):
        super(Handset, self).__init__(*args, **kwargs)
        self.generate_creds()
        self.generate_desc()

    def generate_creds(self):
        if self.cred_user == None:
            self.cred_user = 'ext%s' % ephone_id
        if self.cred_pass == None:
            self.cred_pass = '%s' % ephone_id

    def generate_desc(self):
        if self.desc == None:
            self.desc = '%s Handset %s' % (ephone_type, ephone_id)

    def __repr__(self):
        return '<Handset: %s|%s>' % (self.ephone_id,desc)


class DirNum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    button_id = db.Column(db.Integer, unique=True, nullable=False)
    dual_line = db.Column(db.Boolean, default=True)
    dirnum = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(24))
    name = db.Column(db.String(24))
    pickupgroup = db.Column(db.Integer)
    corlist_in = db.Column(db.Text, default="StandardUser")
    corlist_out = db.Column(db.Text)
    transfer_mode = db.Column(db.String(7), default="consult")
    ephone_dn_templ = db.Column(db.Integer)
    cfg_pickle = db.Column(db.Text)
    last_update_by = db.Column(db.String(10), default="System")
    create_ts = db.Column(db.DateTime, default=datetime.datetime.now)
    update_ts = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __init__(self, *args, **kwargs):
        super(DirNum, self),__init__(*args, **kwargs)
        self.generate_label()
        self.generate_name()

    def generate_label(self):
        if self.label == None:
            self.label = 'Extension %s' % self.dirnum
    
    def generate_label(self):
        if self.name == None:
            self.name = 'Extension %s' % self.dirnum

    def __repr__(self):
        return '<DirNum: %s|%s>' % (self.dirnum, self.name)


