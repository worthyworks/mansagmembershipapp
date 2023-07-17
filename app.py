from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mansag.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=0)
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Member %r>' % self.id

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        specialty = request.form['specialty']
        status = request.form['status']
        
        new_member = Membership(name=name, email=email, specialty=specialty, status=status)

        try:
            db.session.add(new_member)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding this member'
    else:
        members = Membership.query.order_by(Membership.date_subscribed).all()
        return render_template('index.html', members=members)
    
@app.route('/delete/<int:id>')
def delete(id):
    member_to_delete = Membership.query.get_or_404(id)
    
    try:
        db.session.delete(member_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that member'
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    member = Membership.query.get_or_404(id)
    
    if request.method == 'POST':
        member.name = request.form['name']
        member.email = request.form['email']
        member.specialty = request.form['specialty']
        member.status = request.form['status']
        
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating this member'
    else:
        return render_template('update.html', member=member)


if __name__ == "__main__":
    app.run(debug=True)
