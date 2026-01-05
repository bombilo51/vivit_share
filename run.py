from app import create_app
from app.models import Product
from app.extensions import db
from app.utils import normalize_text


app = create_app()

with app.app_context():
    products = Product.query.all()
    for p in products:
        p.name_search = normalize_text(p.name)

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)