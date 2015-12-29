from app import app, db
import models
import views

from handsets.blueprint import handsets
app.register_blueprint(handsets, url_prefix='/handsets')

if __name__ == '__main__':
    app.run()
