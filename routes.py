from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db, login_manager
from models import User, JournalEntry
from flask import abort

bp = Blueprint('routes', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', entries=entries)

@bp.route('/entry/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        experience = request.form['experience']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']

        # Convert string from form to datetime object
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M")

        entry = JournalEntry(
            title=title,
            description=description,
            experience=experience,
            start_time=start_time,
            end_time=end_time,
            author=current_user
        )
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry created!", "success")
        return redirect(url_for("routes.dashboard"))

    return render_template("entry_form.html")

@bp.route('/entry/<int:id>')
@login_required
def view_entry(id):
    entry = JournalEntry.query.get_or_404(id)         # 404 if id not present
    # enforce ownership
    if entry.user_id != current_user.id:
        # hide existence → return 404 to avoid leaking info
        abort(404)
    return render_template('view_entry.html', entry=entry)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))


import csv
from io import StringIO
from flask import Response, request

@bp.route('/download', methods=['GET', 'POST'])
@login_required
def download_entries():
    if request.method == 'POST':
        from_date_str = request.form.get('from_date')
        to_date_str = request.form.get('to_date')

        # Convert strings to datetime objects
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            from_date = to_date = None

        # Filter entries
        query = JournalEntry.query.filter_by(user_id=current_user.id)
        if from_date:
            query = query.filter(JournalEntry.start_time >= from_date)
        if to_date:
            query = query.filter(JournalEntry.end_time <= to_date)

        entries = query.order_by(JournalEntry.start_time).all()

        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Title', 'Description', 'Experience', 'From', 'To'])
        for e in entries:
            writer.writerow([
                e.title,
                e.description,
                e.experience,
                e.start_time.strftime('%Y-%m-%d %H:%M'),
                e.end_time.strftime('%Y-%m-%d %H:%M')
            ])

        # Send CSV as response
        output = si.getvalue()
        return Response(
            output,
            mimetype='text/csv',
            headers={
                "Content-Disposition": f"attachment;filename=journal_entries_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

    return render_template('download.html')
