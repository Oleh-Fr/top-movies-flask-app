from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, select
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# API and Headers
API_ACCESS =TMDB_API_KEY
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_ACCESS}",
}

# Flask and SQLAlchemy fragments
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SECRET_KEY'] = SECRET_KEY
db = SQLAlchemy(app)
Bootstrap5(app)

class ChangeReviewForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10 e.g. 7.3', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField("Done")

class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# CREATE DB
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


# # CREATE TABLE
# with app.app_context():
#     db.create_all()

@app.route("/")
def home():
    movies = Movies.query.order_by(Movies.rating.desc()).all()
    for index, movie in enumerate(movies, start=1):
        movie.ranking = index
    db.session.commit()
    return render_template("index.html", movies=movies)

@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        new_movie = form.title.data
        URL = f'https://api.themoviedb.org/3/search/movie?query={new_movie}&language=en-US&page=1'
        response = requests.get(URL, headers=headers)
        movie = response.json()["results"]
        return render_template("select.html", form=form, movie=movie)
    id = request.args.get('id')
    if id:
        url = f"https://api.themoviedb.org/3/movie/{id}?language=en-US"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return "Error fetching movie data", 500
        else:
            new_movie = Movies(
                title=response.json()["original_title"],
                img_url=f"https://image.tmdb.org/t/p/w500{response.json()['poster_path']}",
                year=int(response.json()["release_date"][:4]),
                description=response.json()["overview"],
                rating=0.0,  # Default rating
                ranking=0,  # Default ranking
                review="",  # Default review
            )
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for('edit', id=new_movie.id))
    return render_template("add.html", form=form)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    form = ChangeReviewForm()
    movie = Movies.query.get_or_404(id)
    if form.validate_on_submit():
        movie.review = form.review.data
        movie.rating = form.rating.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete/<int:id>", methods=['GET', 'POST'])
def delete(id):
    movie = Movies.query.get_or_404(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
