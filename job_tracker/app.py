from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False)
from flask_login import current_user

@app.route('/add_job', methods=['POST'])
@login_required
def add_job():
    company = request.form['company']
    role = request.form['role']
    deadline_str = request.form['deadline']
    status = request.form['status']

    # Convert string to Python date object
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()

    new_job = Job(
        user_id=current_user.id,
        company=company,
        role=role,
        deadline=deadline,
        status=status
    )
    db.session.add(new_job)
    db.session.commit()
    return redirect(url_for('dashboard'))

from flask import request, redirect, url_for, flash

@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        job.company = request.form['company']
        job.role = request.form['role']
        job.deadline = request.form['deadline']  # ensure correct date format
        job.status = request.form['status']
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_job.html', job=job)




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home
from flask import request

@app.route('/', methods=['GET'])
@login_required
def dashboard():
    # Get filter values from URL, default to 'all' and empty string if none given
    status_filter = request.args.get('status', 'all')
    company_filter = request.args.get('company', '')

    # Start query to get jobs of the current user
    query = Job.query.filter_by(user_id=current_user.id)

    # If status is not 'all', filter by status
    if status_filter != 'all':
        query = query.filter(Job.status == status_filter)

    # If company name filter is not empty, filter by company name (case-insensitive)
    if company_filter:
        query = query.filter(Job.company.ilike(f'%{company_filter}%'))

    # Get the filtered list of jobs, ordered by deadline
    jobs = query.order_by(Job.deadline).all()

    # Send jobs and filter values back to template
    return render_template('dashboard.html', jobs=jobs, status_filter=status_filter, company_filter=company_filter)

@app.route('/delete_job/<int:id>')
@login_required
def delete_job(id):
    job = Job.query.get_or_404(id)
    if job.user_id != current_user.id:
        flash("You are not allowed to delete this job.")
        return redirect(url_for('dashboard'))
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!")
    return redirect(url_for('dashboard'))


# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!")
            return redirect(url_for('signup'))
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Check email and password.")
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)