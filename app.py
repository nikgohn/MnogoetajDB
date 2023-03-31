from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

UPLOAD_FOLDER = '/static/img/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HomeInfo.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)


class Home(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    adress = db.Column(db.String(300), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    porch = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(300))
    image = db.Column(db.LargeBinary)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Home %r>' % self.id


#@app.route('/')
#def index():
#    return render_template("index.html")


@app.route('/AddHome', methods=['POST', 'GET'])
def addhome():
    if request.method == "POST":
        year = request.form['year']
        adress = request.form['adress']
        type = request.form['type']
        floor = request.form['floor']
        porch = request.form['porch']
        file = request.files['file']

        home = Home(year=year, adress=adress, type=type, floor=floor, porch=porch, filename=file.filename, image=file.read())

        try:
            db.session.add(home)
            db.session.commit()
            return redirect('/posts')

        except:
            return "При добавлении возникла ошибка"

    else:
        return render_template("AddHome.html")


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
    return render_template("homedata.html", home=home)


@app.route('/posts/<int:id>/delete')
def posts_delete(id):
    home = Home.query.get_or_404(id)

    try:
        db.session.delete(home)
        db.session.commit()
        return redirect('/posts')
    except:
        return 'При удалении произошла ошибка'


@app.route('/posts/<int:id>/edit', methods=['POST', 'GET'])
def posts_edit(id):
    home = Home.query.get(id)
    if request.method == "POST":

        home.year = request.form['year']
        home.adress = request.form['adress']
        home.type = request.form['type']
        home.floor = request.form['floor']
        home.porch = request.form['porch']

        try:

            db.session.commit()
            return redirect('/posts')
        except:
            return "При изменении возникла ошибка"
    else:

        return render_template("edit.html", home=home)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
