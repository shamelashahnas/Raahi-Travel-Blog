from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
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

class ItineraryDay(db.Model):
    __tablename__ = 'itinerary_days'
    day_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itineraries.itinerary_id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    heading = db.Column(db.String(200), nullable=False)  # Add heading field
    description = db.Column(db.Text, nullable=False)
    itinerary = db.relationship('Itinerary', backref=db.backref('itinerary_days', lazy=True))

class TravelEssentials(db.Model):
    __tablename__ = 'travel_essentials'
    travelessential_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    travelessential_name = db.Column(db.String(100))
    travelessential_description = db.Column(db.Text, nullable=False)

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
    cover_image = request.files.get('cover_image')

    if cover_image and cover_image.filename:
        image_filename = secure_filename(cover_image.filename)
        try:
            cover_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        except Exception as e:
            # Handle the error (log it, notify the user, etc.)
            print(f"Error saving image: {e}")
            return redirect(url_for('error_page'))  # Redirect to an error page or show an error message
    else:
        image_filename = None

    try:
        new_destination = Destination(destination_name=name, description=description, cover_image=image_filename)
        db.session.add(new_destination)
        db.session.commit()
    except Exception as e:
        # Handle the error (log it, notify the user, etc.)
        print(f"Error saving destination: {e}")
        return redirect(url_for('error_page'))  # Redirect to an error page or show an error message

    return redirect(url_for('dashboard'))
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_blog', methods=['POST'])
def add_blog():
    title = request.form['blog_title']
    content = request.form['content']
    destination_id = request.form['destination_id']

    # Retrieve subheadings and descriptions from the form
    subheadings_titles = request.form.getlist('subheading[]')
    subheadings_descriptions = request.form.getlist('subheading_description[]')

    # Create the new blog
    new_blog = Blog(blog_title=title, content=content, destination_id=destination_id)
    db.session.add(new_blog)
    db.session.commit()

    # Save subheadings and descriptions
    for title, description in zip(subheadings_titles, subheadings_descriptions):
        if title and description:
            new_subheading = Subheading(
                subheading_title=title,
                description=description,
                blog_id=new_blog.blog_id
            )
            db.session.add(new_subheading)

    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_image', methods=['POST'])
def add_image():
    image_file = request.files.get('image_file')
    description = request.form['image_description']
    associated_blog = request.form.get('associated_blog')
    associated_destination = request.form.get('associated_destination')

    if image_file and image_file.filename:
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image_file.save(image_path)

        new_image = Image(url=image_filename, description=description, blog_id=associated_blog, destination_id=associated_destination)
        db.session.add(new_image)
        db.session.commit()
    
    return redirect(url_for('dashboard'))
@app.route('/add_itinerary', methods=['POST'])
def add_itinerary():
    destination_id = request.form.get('destination_id')
    days = request.form.get('days')
    description = request.form.get('description')

    # Validate input
    if not destination_id or not days or not description:
        flash('All fields are required', 'danger')
        return redirect(url_for('select_itinerary'))

    try:
        days = int(days)
    except (ValueError, TypeError):
        flash('Invalid number of days', 'danger')
        return redirect(url_for('select_itinerary'))

    # Create the new itinerary
    new_itinerary = Itinerary(destination_id=destination_id, days=days, description=description)
    db.session.add(new_itinerary)
    db.session.commit()

    # Add individual day headings and descriptions
    for i in range(1, days + 1):
        heading = request.form.get(f'day_{i}_heading')
        day_description = request.form.get(f'day_{i}_description')

        if heading and day_description:
            new_itinerary_day = ItineraryDay(
                itinerary_id=new_itinerary.itinerary_id,
                day_number=i,
                heading=heading,
                description=day_description
            )
            db.session.add(new_itinerary_day)
        else:
            flash(f"Missing details for Day {i}", 'danger')
            db.session.rollback()
            return redirect(url_for('select_itinerary'))
    
    db.session.commit()
    flash('Itinerary added successfully', 'success')
    return redirect(url_for('dashboard'))


@app.route('/add_travel_essential', methods=['POST'])
def add_travel_essential():
    essential_name = request.form.get('essential_name')
    essential_description = request.form.get('essential_description')

    if not essential_name or not essential_description:
        flash('All fields are required', 'danger')
        return redirect(url_for('dashboard'))

    try:
        new_essential = TravelEssentials(
            travelessential_name=essential_name,
            travelessential_description=essential_description
        )
        db.session.add(new_essential)
        db.session.commit()
        flash('Travel essential added successfully!', 'success')
    except Exception as e:
        print(f"Error adding travel essential: {e}")
        flash('Error adding travel essential', 'danger')

    return redirect(url_for('dashboard'))



@app.route('/dashboard', endpoint='dashboard')
def admin_dashboard():
    destinations = Destination.query.all()
    blogs = Blog.query.all()  # Fetch all blogs from the database
    return render_template('dashboard.html', destinations=destinations, blogs=blogs)

@app.route('/', endpoint='home')
def home():
    return render_template('home.html')
@app.route('/destinations', endpoint='destinations')
def destinations():
    destinations = Destination.query.all()  # Fetch all destinations from the database
    return render_template('destinations.html', destinations=destinations)

@app.route('/destination/<int:destination_id>')
def destination_detail(destination_id):
    # Fetch the destination by ID
    destination = Destination.query.get_or_404(destination_id)
    
    # Fetch blogs related to this destination
    blogs = Blog.query.filter_by(destination_id=destination_id).all()
    
    return render_template('destination_details.html', destination=destination, blogs=blogs)

@app.route('/blog/<int:blog_id>')
def blog_detail(blog_id):
    # Fetch the blog by ID
    blog = Blog.query.get_or_404(blog_id)
    
    # Fetch related subheadings
    subheadings = Subheading.query.filter_by(blog_id=blog_id).all()
    
    # Fetch related images
    images = Image.query.filter_by(blog_id=blog_id).all()
    
    return render_template('blog.html', blog=blog, subheadings=subheadings, images=images)


@app.route('/select_itinerary', methods=['GET', 'POST'])
def select_itinerary():
    destinations = Destination.query.all()
    selected_destination = None
    itinerary = None
    itinerary_days = []  # Initialize itinerary_days

    if request.method == 'POST':
        destination_id = request.form.get('destination_id')
        selected_destination = Destination.query.get(destination_id)
        itinerary = Itinerary.query.filter_by(destination_id=destination_id).first()
        if itinerary:
            itinerary_days = ItineraryDay.query.filter_by(itinerary_id=itinerary.itinerary_id).order_by(ItineraryDay.day_number).all()

    return render_template(
        'select_itinerary.html',
        destinations=destinations,
        selected_destination=selected_destination,
        itinerary=itinerary,
        itinerary_days=itinerary_days
    )
@app.route('/travel_essentials')
def travel_essentials():
    essentials = TravelEssentials.query.all()  # Fetch all travel essentials from the database
    return render_template('travel_essentials.html', essentials=essentials)



if __name__ == '__main__':
    app.run(debug=True)
