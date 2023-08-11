from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime,timedelta
from flask_mail import Mail, Message


from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask import flash
import yagmail



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mansag.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['MAIL_SERVER'] = 'smtp.mail.google.com'
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USE_TLS'] = True  
app.config['MAIL_USERNAME'] = 'mansagmembership@gmail.com'
app.config['MAIL_PASSWORD'] = 'isvuxbwjhamiwizu'
mail = Mail(app)

app.config['SECRET_KEY'] = 'your_secret_key_here'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    return None

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for('index'))
        
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))





class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=0)
    date_subscribed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<Member %r>' % self.id
    
def is_subscription_expired(date_subscribed):
    current_date = datetime.utcnow().date()
    expiration_date = date_subscribed.date() + timedelta(days=365)
    return expiration_date < current_date

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        specialty = request.form['specialty']
        status = request.form['status']
        date_subscribed = datetime.strptime(request.form['date_subscribed'], '%Y-%m-%d')
        
        new_member = Membership(name=name, email=email, specialty=specialty, status=status, date_subscribed=date_subscribed)

        try:
            db.session.add(new_member)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding this member'
    else:
        query = Membership.query.order_by(Membership.date_subscribed)
        
        search_name = request.args.get('name')
        search_specialty = request.args.get('specialty')
        search_status = request.args.get('status')
        
        if search_name:
            query = query.filter(Membership.name.ilike(f'%{search_name}%'))
        if search_specialty:
            query = query.filter(Membership.specialty.ilike(f'%{search_specialty}%'))
        if search_status:
            query = query.filter(Membership.status == int(search_status))
        
        members = query.all()
        
        return render_template('index.html', members=members, is_subscription_expired=is_subscription_expired)
    
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    member_to_delete = Membership.query.get_or_404(id)
    
    try:
        db.session.delete(member_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that member'
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    member = Membership.query.get_or_404(id)

    if request.method == 'POST':
        member.name = request.form['name']
        member.email = request.form['email']
        member.specialty = request.form['specialty']
        member.status = request.form['status']
        
        member.date_subscribed = datetime.strptime(request.form['date_subscribed'], '%Y-%m-%d')

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating this member'
    else:
        return render_template('update.html', member=member)

@app.route('/send_emails', methods=['GET', 'POST'])
def send_emails():
    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        recipients_list = [member.email for member in Membership.query.all()]
        
        try:
            yag = yagmail.SMTP('mansagmembership@gmail.com', 'isvuxbwjhamiwizu')

            
            with app.app_context():
                for recipient in recipients_list:
                    yag.send(to=recipient, subject=subject, contents=body)
            
            
            yag.close()
            
            flash('Emails sent successfully', 'success')
        except Exception as e:
            flash('Error sending emails. Please check your email settings and try again.', 'error')  # Show error message as a popup
    
    return render_template('send_emails.html')



if __name__ == "__main__":
    app.run(debug=False)