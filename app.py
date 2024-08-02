from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/raahi_travelblog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Needed for flash messages
app.config['UPLOAD_FOLDER'] = 'uploads'  # or an absolute path

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class UserAdmin(db.Model):
    __tablename__ = 'user_admin'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(200), nullable=False, unique=True)
    user_password = db.Column(db.String(100), nullable=False)

class Destination(db.Model):
    __tablename__ = 'destinations'
    destination_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    destination_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(200), nullable=True)
    location_detail = db.relationship('LocationDetail', backref='destination', uselist=False)
    blogs = db.relationship('Blog', backref='destination', lazy=True)

class Blog(db.Model):
    __tablename__ = 'blogs'
    blog_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    blog_title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.destination_id'))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    images = db.relationship('Image', backref='blog', lazy=True)

class Subheading(db.Model):
    __tablename__ = 'subheadings'
    subheading_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subheading_title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.blog_id'), nullable=False)
    blog = db.relationship('Blog', backref=db.backref('subheadings', lazy=True))


class Image(db.Model):
    __tablename__ = 'images'
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.blog_id'), nullable=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.destination_id'), nullable=True)

class LocationDetail(db.Model):
    __tablename__ = 'location_details'
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.destination_id'))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    local_tips = db.Column(db.Text, nullable=True)
    best_time_to_visit = db.Column(db.String(100), nullable=True)

class Itinerary(db.Model):
    __tablename__ = 'itineraries'
    itinerary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.destination_id'))
    days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)

class TravelEssentials(db.Model):
    __tablename__ = 'travel_essentials'
    travelessential_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    travelessential_name = db.Column(db.String(100))
    travelessential_description = db.Column(db.String(100))

@app.route('/useradmin', methods=['GET', 'POST'])
def useradmin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Find user by email
        user = UserAdmin.query.filter_by(user_email=email).first()
        
        # Check if user exists and password is correct
        if user:
            if user.user_password == password:
                session['user_id'] = user.user_id  # Store user ID in session
                return redirect(url_for('dashboard'))  # Redirect to the dashboard or desired page
            else:
                flash('Invalid email or password', 'danger')
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('user.html')

@app.route('/userregister', methods=['GET', 'POST'])
def userregister():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Store the user in the database
        new_user = UserAdmin(user_email=email, user_password=password)
        db.session.add(new_user)
        db.session.commit()
    return render_template('user_reg.html')

@app.route('/add_destination', methods=['POST'])
def add_destination():
    name = request.form['destination_name']
    description = request.form['description']
    cover_image = request.files.get('cover_image')  # Use .get() to avoid KeyError

    if cover_image and cover_image.filename:
        image_filename = secure_filename(cover_image.filename)
        cover_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
    else:
        image_filename = None

    new_destination = Destination(destination_name=name, description=description, cover_image=image_filename)
    db.session.add(new_destination)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_blog', methods=['POST'])
def add_blog():
    title = request.form['blog_title']
    content = request.form['content']
    destination_id = request.form['destination_id']
    images = request.files.getlist('images')  # Get list of image files

    # Create the new blog
    new_blog = Blog(blog_title=title, content=content, destination_id=destination_id)
    db.session.add(new_blog)
    db.session.commit()

    # Save images and add to database
    for image in images:
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            new_image = Image(url=image_filename, blog_id=new_blog.blog_id)
            db.session.add(new_image)

    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_itinerary', methods=['POST'])
def add_itinerary():
    destination_id = request.form['destination_id']
    days = request.form['days']
    description = request.form['description']
    new_itinerary = Itinerary(destination_id=destination_id, days=days, description=description)
    db.session.add(new_itinerary)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_travelessential', methods=['POST'])
def add_travelessential():
    name = request.form['travelessential_name']
    description = request.form['travelessential_description']
    new_travel_essential = TravelEssentials(travelessential_name=name, travelessential_description=description)
    db.session.add(new_travel_essential)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard', endpoint='dashboard')
def admin_dashboard():
    destinations = Destination.query.all()
    return render_template('dashboard.html', destinations=destinations)

@app.route('/', endpoint='home')
def home():
    return render_template('home.html')

@app.route('/destinations', endpoint='destinations')
def destinations():
    return render_template('destinations.html')

if __name__ == '__main__':
    app.run(debug=True)
