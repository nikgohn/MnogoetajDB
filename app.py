from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from base64 import b64encode
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HomeInfo.db'
db = SQLAlchemy(app)


class Home(db.Model):
    __tablename__ = "Home_data"
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    floors = db.relationship('Floor', backref='home')
    porch = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(300))
    image = db.Column(db.LargeBinary)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    adress_data = db.relationship('Adress', backref='home')


class Adress(db.Model):
    __tablename__ = "Adress_data"
    id = db.Column(db.Integer, primary_key=True)
    home_id = db.Column(db.Integer, db.ForeignKey('Home_data.id'))
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=True)
    street = db.Column(db.String(300), nullable=False)
    homenum = db.Column(db.Integer, nullable=True)


class Floor(db.Model):
    __tablename__ = "Floor_data"
    id = db.Column(db.Integer, primary_key=True)
    home_id = db.Column(db.Integer, db.ForeignKey('Home_data.id'))
    number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300), nullable=True)
    filename = db.Column(db.String(300))
    image = db.Column(db.LargeBinary)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Floor %r>' % self.id


with app.app_context():
    db.create_all()


@app.route('/AddHome', methods=['POST', 'GET'])
def addhome():
    current_year = datetime.now().year

    if request.method == "POST":
        year = request.form['year']
        type = request.form['type']
        floor = request.form['floor']
        porch = request.form['porch']
        file = request.files['file']
        city = request.form['city']
        district = request.form['district']
        street = request.form['street']
        homenum = request.form['homenum']
        floor_numbers = request.form.getlist('floor_number')
        floor_descriptions = request.form.getlist('floor_description')
        floor_images = request.files.getlist('floor_image')

        home = Home(year=year, type=type, floor=floor, porch=porch, filename=file.filename, image=file.read())
        adress_data = Adress(city=city, district=district, street=street, homenum=homenum, home=home)

        try:
            db.session.add(home)
            db.session.add(adress_data)
            db.session.commit()

            for i in range(len(floor_numbers)):
                floor_number = floor_numbers[i]
                floor_description = floor_descriptions[i]
                floor_image = floor_images[i]

                floor = Floor(number=floor_number, description=floor_description, filename=floor_image.filename, image=floor_image.read())
                floor.home_id = home.id  # Set the home_id for the floor object
                db.session.add(floor)

            db.session.commit()
            return redirect('/posts')

        except:
            return "При добавлении возникла ошибка"

    else:
        return render_template('AddHome.html', current_year=current_year)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/posts')
@app.route('/')
def posts():
    homelist = Home.query.order_by(Home.date.desc()).all()
    return render_template("posts.html", homelist=homelist)


@app.route('/posts/<int:id>')
def posts_data(id):
    home = Home.query.get(id)
    bimg = b64encode(home.image)
    image = bimg.decode('utf-8')
    address = Adress.query.filter_by(home_id=id).first()
    floors = Floor.query.filter_by(home_id=id).all()

    for floor in floors:
        floor.b64image = b64encode(floor.image).decode('utf-8')

    return render_template("homedata.html", home=home, address=address, image=image, floors=floors)


@app.route('/posts/<int:id>/delete')
def posts_delete(id):
    home = Home.query.get_or_404(id)

    try:
        address = Adress.query.filter_by(home_id=id).first()
        floors = Floor.query.filter_by(home_id=id).all()

        for floor in floors:
            db.session.delete(floor)

        db.session.delete(address)
        db.session.delete(home)
        db.session.commit()

        return redirect('/posts')
    except:
        return 'При удалении произошла ошибка'


@app.route('/posts/<int:id>/edit', methods=['POST', 'GET'])
def posts_edit(id):
    home = Home.query.get(id)
    address = Adress.query.filter_by(home_id=id).first()
    bimg = b64encode(home.image)
    image = bimg.decode('utf-8')

    current_year = datetime.now().year

    if request.method == "POST":
        home.year = request.form['year']
        home.type = request.form['type']
        home.floor = request.form['floor']
        home.porch = request.form['porch']

        address.city = request.form['city']
        address.district = request.form['district']
        address.street = request.form['street']
        address.homenum = request.form['homenum']

        file = request.files.get('file')
        if file:
            home.filename = file.filename
            home.image = file.read()

        # Update existing floors
        for floor in home.floors:
            floor_number = request.form.get(f'floor_number_{floor.id}')
            floor_description = request.form.get(f'floor_description_{floor.id}')
            floor_image = request.files.get(f'floor_image_{floor.id}')

            if floor_number is not None:
                floor.number = floor_number
            if floor_description is not None:
                floor.description = floor_description
            if floor_image:
                floor.filename = floor_image.filename
                floor.image = floor_image.read()

        # Add new floors
        floor_numbers = request.form.getlist('floor_number')
        floor_descriptions = request.form.getlist('floor_description')
        floor_images = request.files.getlist('floor_image')

        for i in range(len(floor_numbers)):
            floor_number = floor_numbers[i]
            floor_description = floor_descriptions[i]
            floor_image = floor_images[i]

            if floor_number and floor_description and floor_image:
                floor = Floor(number=floor_number, description=floor_description, filename=floor_image.filename, image=floor_image.read())
                floor.home_id = home.id
                db.session.add(floor)

        try:
            db.session.commit()
            return redirect('/posts')
        except:
            return "При изменении возникла ошибка"
    else:
        # Get existing floors' images
        for floor in home.floors:
            floor.b64image = b64encode(floor.image).decode('utf-8')

        return render_template("edit.html", home=home, address=address, current_year=current_year, image=image)


if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", default=5000))
