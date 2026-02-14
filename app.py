from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

# =================== APP SETUP ===================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chandrika-jain-college-2024-secret')

# ✅ DATABASE - Supabase PostgreSQL (Permanent) or SQLite (Fallback)
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    STORAGE_TYPE = 'PostgreSQL (Permanent) ✅'
    print("✅ Using Supabase PostgreSQL (PERMANENT)")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/college.db'
    STORAGE_TYPE = 'SQLite (Temporary) ⚠️'
    print("⚠️ Using SQLite (Set DATABASE_URL for permanent storage)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# =================== DATABASE MODELS ===================
class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default='teacher')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20))
    course = db.Column(db.String(100))
    drive_link = db.Column(db.String(500), nullable=False)
    download_link = db.Column(db.String(500))
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.String(120))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    exam_type = db.Column(db.String(100))
    course = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    year = db.Column(db.String(10))
    drive_link = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.String(120))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    attachment_link = db.Column(db.String(500))
    is_important = db.Column(db.Boolean, default=False)
    posted_by = db.Column(db.String(120))
    post_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    qualification = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    photo_url = db.Column(db.String(500))
    experience = db.Column(db.String(50))
    specialization = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20))
    duration = db.Column(db.String(50))
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    seats = db.Column(db.Integer)
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

class Gallery(db.Model):
    __tablename__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    image_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    try:
        return Admin.query.get(int(user_id))
    except:
        return None

# =================== HELPERS ===================
def convert_drive_link(link):
    if not link:
        return {'preview': '', 'download': '', 'view': ''}
    if 'drive.google.com' in str(link):
        file_id = None
        if '/file/d/' in link:
            file_id = link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in link:
            file_id = link.split('id=')[1].split('&')[0]
        if file_id:
            return {
                'preview': f'https://drive.google.com/file/d/{file_id}/preview',
                'download': f'https://drive.google.com/uc?export=download&id={file_id}',
                'view': f'https://drive.google.com/file/d/{file_id}/view'
            }
    return {'preview': link, 'download': link, 'view': link}

def convert_drive_image(link):
    if not link:
        return ''
    if 'drive.google.com' in str(link):
        file_id = None
        if '/file/d/' in link:
            file_id = link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in link:
            file_id = link.split('id=')[1].split('&')[0]
        if file_id:
            return f'https://drive.google.com/uc?export=view&id={file_id}'
    return link

def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tables created!")

            if not Admin.query.filter_by(username='admin').first():
                db.session.add(Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    name='Principal - CJDM', role='admin'
                ))
                db.session.add(Admin(
                    username='teacher1',
                    password_hash=generate_password_hash('teacher123'),
                    name='Sample Teacher', role='teacher'
                ))

                for c in [
                    {'name': 'Bachelor of Arts (BA)', 'code': 'BA', 'duration': '3 Years',
                     'department': 'Arts', 'seats': 120,
                     'description': 'BA with Hindi, English, Political Science, History, Economics, Sociology.',
                     'eligibility': '10+2 Pass from any recognized board'},
                    {'name': 'Bachelor of Science (BSc)', 'code': 'BSC', 'duration': '3 Years',
                     'department': 'Science', 'seats': 60,
                     'description': 'BSc with Physics, Chemistry, Mathematics, Biology.',
                     'eligibility': '10+2 Pass with Science stream'},
                    {'name': 'Bachelor of Commerce (BCom)', 'code': 'BCOM', 'duration': '3 Years',
                     'department': 'Commerce', 'seats': 60,
                     'description': 'BCom with Accounting, Business Studies, Economics.',
                     'eligibility': '10+2 Pass with Commerce or any stream'},
                ]:
                    db.session.add(Course(**c))

                db.session.add(Notice(
                    title='Welcome to Chandrika Jain Degree Mahavidyalaya!',
                    content='Official website launched. Access library, results, notices online.',
                    category='General', is_important=True, posted_by='Admin'
                ))
                db.session.add(Notice(
                    title='Digital Library Now Available',
                    content='Free digital books and study materials for all students.',
                    category='General', is_important=True, posted_by='Admin'
                ))
                db.session.commit()
                print("✅ Default data inserted!")
            else:
                print("✅ Database already initialized")
        except Exception as e:
            print(f"❌ DB Error: {e}")
            try:
                db.session.rollback()
            except:
                pass

# =================== PUBLIC ROUTES ===================
@app.route('/')
def index():
    try:
        notices = Notice.query.filter_by(is_active=True).order_by(Notice.post_date.desc()).limit(5).all()
        courses = Course.query.filter_by(is_active=True).all()
        gallery = Gallery.query.filter_by(is_active=True).order_by(Gallery.upload_date.desc()).limit(6).all()
    except:
        notices, courses, gallery = [], [], []
    return render_template('index.html', notices=notices, courses=courses, gallery=gallery)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
def courses():
    try:
        all_courses = Course.query.filter_by(is_active=True).all()
    except:
        all_courses = []
    return render_template('courses.html', courses=all_courses)

@app.route('/faculty')
def faculty():
    try:
        all_faculty = Faculty.query.filter_by(is_active=True).all()
        departments = [d[0] for d in db.session.query(Faculty.department).filter_by(is_active=True).distinct().all() if d[0]]
    except:
        all_faculty, departments = [], []
    return render_template('faculty.html', faculty=all_faculty, departments=departments)

@app.route('/library')
def library():
    try:
        subject = request.args.get('subject', '')
        course = request.args.get('course', '')
        semester = request.args.get('semester', '')
        search = request.args.get('search', '')
        query = Book.query.filter_by(is_active=True)
        if subject: query = query.filter(Book.subject.ilike(f'%{subject}%'))
        if course: query = query.filter(Book.course.ilike(f'%{course}%'))
        if semester: query = query.filter_by(semester=semester)
        if search:
            query = query.filter(db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%'),
                Book.subject.ilike(f'%{search}%')
            ))
        books = query.order_by(Book.upload_date.desc()).all()
        subjects = [s[0] for s in db.session.query(Book.subject).filter_by(is_active=True).distinct().all() if s[0]]
        courses_list = [c[0] for c in db.session.query(Book.course).filter_by(is_active=True).distinct().all() if c[0]]
    except:
        books, subjects, courses_list = [], [], []
    return render_template('library.html', books=books, subjects=subjects,
                         courses=courses_list, convert_drive_link=convert_drive_link)

@app.route('/results')
def results():
    try:
        all_results = Result.query.filter_by(is_active=True).order_by(Result.upload_date.desc()).all()
    except:
        all_results = []
    return render_template('results.html', results=all_results, convert_drive_link=convert_drive_link)

@app.route('/gallery')
def gallery():
    try:
        category = request.args.get('category', '')
        query = Gallery.query.filter_by(is_active=True)
        if category: query = query.filter_by(category=category)
        images = query.order_by(Gallery.upload_date.desc()).all()
        categories = [c[0] for c in db.session.query(Gallery.category).filter_by(is_active=True).distinct().all() if c[0]]
    except:
        images, categories = [], []
    return render_template('gallery.html', images=images, categories=categories)

@app.route('/notices')
def notices():
    try:
        all_notices = Notice.query.filter_by(is_active=True).order_by(Notice.post_date.desc()).all()
    except:
        all_notices = []
    return render_template('notices.html', notices=all_notices)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            db.session.add(ContactMessage(
                name=request.form['name'], email=request.form['email'],
                phone=request.form.get('phone', ''), subject=request.form.get('subject', ''),
                message=request.form['message']
            ))
            db.session.commit()
            flash('Message sent successfully!', 'success')
        except:
            db.session.rollback()
            flash('Error sending message.', 'error')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# =================== ADMIN ===================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        try:
            user = Admin.query.filter_by(username=request.form['username']).first()
            if user and check_password_hash(user.password_hash, request.form['password']):
                login_user(user)
                flash(f'Welcome {user.name}!', 'success')
                return redirect(url_for('admin_dashboard'))
            flash('Invalid credentials!', 'error')
        except:
            flash('Login error!', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    try:
        stats = {k: globals()[v[0]].query.filter_by(**v[1]).count() for k, v in {
            'books': (Book, {'is_active': True}), 'results': (Result, {'is_active': True}),
            'notices': (Notice, {'is_active': True}), 'faculty': (Faculty, {'is_active': True}),
            'courses': (Course, {'is_active': True}), 'gallery': (Gallery, {'is_active': True}),
        }.items()}
        stats['messages'] = ContactMessage.query.filter_by(is_read=False).count()
    except:
        stats = {k: 0 for k in ['books','results','notices','faculty','courses','messages','gallery']}

    try:
        stats = {
            'books': Book.query.filter_by(is_active=True).count(),
            'results': Result.query.filter_by(is_active=True).count(),
            'notices': Notice.query.filter_by(is_active=True).count(),
            'faculty': Faculty.query.filter_by(is_active=True).count(),
            'courses': Course.query.filter_by(is_active=True).count(),
            'messages': ContactMessage.query.filter_by(is_read=False).count(),
            'gallery': Gallery.query.filter_by(is_active=True).count(),
        }
        recent_notices = Notice.query.order_by(Notice.post_date.desc()).limit(5).all()
        recent_messages = ContactMessage.query.order_by(ContactMessage.date.desc()).limit(5).all()
    except:
        stats = {k: 0 for k in ['books','results','notices','faculty','courses','messages','gallery']}
        recent_notices, recent_messages = [], []

    return render_template('admin/dashboard.html', stats=stats,
                         recent_notices=recent_notices, recent_messages=recent_messages,
                         storage_type=STORAGE_TYPE)

@app.route('/admin/books')
@login_required
def manage_books():
    books = Book.query.order_by(Book.upload_date.desc()).all() if True else []
    return render_template('admin/manage_books.html', books=books)

@app.route('/admin/books/add', methods=['POST'])
@login_required
def add_book():
    try:
        b = Book(title=request.form['title'], author=request.form['author'],
                subject=request.form['subject'], semester=request.form.get('semester',''),
                course=request.form.get('course',''), drive_link=request.form['drive_link'],
                description=request.form.get('description',''), uploaded_by=current_user.name)
        b.download_link = convert_drive_link(b.drive_link)['download']
        db.session.add(b); db.session.commit()
        flash('✅ Book added!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_books'))

@app.route('/admin/books/delete/<int:id>')
@login_required
def delete_book(id):
    try:
        Book.query.get_or_404(id).is_active = False; db.session.commit()
        flash('Removed!', 'success')
    except: db.session.rollback()
    return redirect(url_for('manage_books'))

@app.route('/admin/results')
@login_required
def manage_results():
    return render_template('admin/manage_results.html',
                         results=Result.query.order_by(Result.upload_date.desc()).all())

@app.route('/admin/results/add', methods=['POST'])
@login_required
def add_result():
    try:
        db.session.add(Result(title=request.form['title'],
            exam_type=request.form.get('exam_type',''), course=request.form.get('course',''),
            semester=request.form.get('semester',''), year=request.form.get('year',''),
            drive_link=request.form['drive_link'], uploaded_by=current_user.name))
        db.session.commit(); flash('✅ Result uploaded!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_results'))

@app.route('/admin/results/delete/<int:id>')
@login_required
def delete_result(id):
    try: Result.query.get_or_404(id).is_active = False; db.session.commit(); flash('Removed!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_results'))

@app.route('/admin/notices')
@login_required
def manage_notices():
    return render_template('admin/manage_notices.html',
                         notices=Notice.query.order_by(Notice.post_date.desc()).all())

@app.route('/admin/notices/add', methods=['POST'])
@login_required
def add_notice():
    try:
        db.session.add(Notice(title=request.form['title'], content=request.form['content'],
            category=request.form.get('category','General'),
            attachment_link=request.form.get('attachment_link',''),
            is_important='is_important' in request.form, posted_by=current_user.name))
        db.session.commit(); flash('✅ Notice posted!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_notices'))

@app.route('/admin/notices/delete/<int:id>')
@login_required
def delete_notice(id):
    try: Notice.query.get_or_404(id).is_active = False; db.session.commit(); flash('Removed!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_notices'))

@app.route('/admin/faculty')
@login_required
def manage_faculty():
    return render_template('admin/manage_faculty.html',
                         faculty=Faculty.query.filter_by(is_active=True).all())

@app.route('/admin/faculty/add', methods=['POST'])
@login_required
def add_faculty():
    try:
        photo = convert_drive_image(request.form.get('photo_url',''))
        db.session.add(Faculty(name=request.form['name'],
            designation=request.form.get('designation',''),
            department=request.form.get('department',''),
            qualification=request.form.get('qualification',''),
            email=request.form.get('email',''), phone=request.form.get('phone',''),
            photo_url=photo, experience=request.form.get('experience',''),
            specialization=request.form.get('specialization','')))
        db.session.commit(); flash('✅ Faculty added!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_faculty'))

@app.route('/admin/faculty/delete/<int:id>')
@login_required
def delete_faculty(id):
    try: Faculty.query.get_or_404(id).is_active = False; db.session.commit(); flash('Removed!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_faculty'))

@app.route('/admin/gallery')
@login_required
def manage_gallery():
    return render_template('admin/manage_gallery.html',
                         images=Gallery.query.filter_by(is_active=True).order_by(Gallery.upload_date.desc()).all())

@app.route('/admin/gallery/add', methods=['POST'])
@login_required
def add_gallery():
    try:
        db.session.add(Gallery(title=request.form.get('title',''),
            image_url=convert_drive_image(request.form['image_url']),
            category=request.form.get('category','Campus')))
        db.session.commit(); flash('✅ Image added!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_gallery'))

@app.route('/admin/gallery/delete/<int:id>')
@login_required
def delete_gallery(id):
    try: Gallery.query.get_or_404(id).is_active = False; db.session.commit(); flash('Removed!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_gallery'))

@app.route('/admin/courses')
@login_required
def manage_courses():
    return render_template('admin/manage_courses.html',
                         courses=Course.query.filter_by(is_active=True).all())

@app.route('/admin/courses/add', methods=['POST'])
@login_required
def add_course():
    try:
        db.session.add(Course(name=request.form['name'], code=request.form.get('code',''),
            duration=request.form.get('duration',''), description=request.form.get('description',''),
            eligibility=request.form.get('eligibility',''),
            seats=int(request.form.get('seats',0)) if request.form.get('seats') else 0,
            department=request.form.get('department','')))
        db.session.commit(); flash('✅ Course added!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_courses'))

@app.route('/admin/courses/delete/<int:id>')
@login_required
def delete_course(id):
    try: Course.query.get_or_404(id).is_active = False; db.session.commit(); flash('Removed!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_courses'))

@app.route('/admin/messages')
@login_required
def admin_messages():
    return render_template('admin/messages.html',
                         messages=ContactMessage.query.order_by(ContactMessage.date.desc()).all())

@app.route('/admin/messages/read/<int:id>')
@login_required
def mark_read(id):
    try: ContactMessage.query.get_or_404(id).is_read = True; db.session.commit()
    except: db.session.rollback()
    return redirect(url_for('admin_messages'))

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied!', 'error'); return redirect(url_for('admin_dashboard'))
    return render_template('admin/manage_users.html', users=Admin.query.all())

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied!', 'error'); return redirect(url_for('admin_dashboard'))
    try:
        if Admin.query.filter_by(username=request.form['username']).first():
            flash('Username exists!', 'error'); return redirect(url_for('manage_users'))
        db.session.add(Admin(username=request.form['username'],
            password_hash=generate_password_hash(request.form['password']),
            name=request.form['name'], role=request.form.get('role','teacher')))
        db.session.commit(); flash('✅ User created!', 'success')
    except Exception as e:
        db.session.rollback(); flash(f'Error: {e}', 'error')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:id>')
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error'); return redirect(url_for('admin_dashboard'))
    if id == current_user.id:
        flash('Cannot delete yourself!', 'error'); return redirect(url_for('manage_users'))
    try: db.session.delete(Admin.query.get_or_404(id)); db.session.commit(); flash('Deleted!','success')
    except: db.session.rollback()
    return redirect(url_for('manage_users'))

# =================== CONTEXT & ERRORS ===================
@app.context_processor
def utility_processor():
    return {'now': datetime.utcnow, 'convert_drive_image': convert_drive_image}

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    return redirect(url_for('index'))

# =================== RUN ===================
print("\n" + "="*50)
print("🎓 Chandrika Jain Degree Mahavidyalaya")
print("📍 Borda, Kalahandi, Odisha")
print(f"💾 Storage: {STORAGE_TYPE}")
print("="*50 + "\n")

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)
