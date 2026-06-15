from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask import Flask, render_template, redirect, url_for, session, flash
app = Flask(__name__, template_folder='app_templates')
app.secret_key = "finot_super_secret_key"

# ዳታቤዝ እና የፋይል መጫኛ ማውጫ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "finot_data.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')

db = SQLAlchemy(app)

# 📂 1. ለአድሚን ፖስቶች ዳታቤዝ (Text, Picture, Video, Sound)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(300), nullable=True) # የፋይሉ መገኛ
    file_type = db.Column(db.String(50), nullable=True)  # 'image', 'video', 'audio'
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# ✉️ 2. የረዱት ሰዎች (Contact Message) ዳታቤዝ
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)

# --- የዌብሳይቱ ገጾች መስመሮች (Routes) ---

@app.route('/')
def home():
    all_posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('home.html', posts=all_posts)
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/address')
def address():
    return render_template('address.html')
@app.route('/vision')
def vision():
    return render_template('vision.html')

@app.route('/mission')
def mission():
    return render_template('mission.html')

@app.route('/goal')
def goal():
    return render_template('goal.html')
@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        new_msg = ContactMessage(
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            message=request.form.get('message')
        )
        db.session.add(new_msg)
        db.session.commit()
        flash("መልዕክትዎ በተሳካ ሁኔታ ለአድሚኑ ደርሷል!")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# --- 🔐 የአድሚን መቆጣጠሪያ ክፍሎች (Admin Panel) ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Finot@2026Pass"

# 🚪 1. የአድሚን ሎጊን መግቢያ ገጽ (Login Route)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash("በተሳካ ሁኔታ ገብተዋል!")
            return redirect(url_for('admin_dashboard')) # 👈 ወደ /admin ይወስደዋል
        else:
            flash("የተሳሳተ ስም ወይም ፓስወርድ ነው!")
            
    return render_template('admin_login.html')
@app.route('/admin')
def admin_dashboard():
    # 🔒 መጀመሪያ አድሚኑ መግባቱን በ session ያረጋግጣል
    if not session.get('logged_in'):
        flash("እባክዎ መጀመሪያ ይግቡ!")
        return redirect(url_for('admin_login')) # ወደ ሎጊን ገጽ ይወስደዋል
        
    # አድሚኑ ከገባ ደግሞ እነዚህን መረጃዎች ከዳታቤዝ አውጥቶ ያሳየዋል
    all_posts = Post.query.order_by(Post.date_posted.desc()).all()
    all_messages = ContactMessage.query.order_by(ContactMessage.date_sent.desc()).all()
    return render_template('admin.html', posts=all_posts, messages=all_messages)
# 🆕 አዲስ ፖስት መለጠፊያ (ጽሑፍ + ፋይል)
@app.route('/admin/post/add', methods=['POST'])
def add_post():
    title = request.form.get('title')
    content = request.form.get('content')
    file = request.files.get('file')
    
    file_path = None
    file_type = None
    
    if file and file.filename != '':
        # ፎልደሩ ከሌለ መፍጠር
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_path = f'uploads/{filename}'
        
        # የፋይል አይነት መለየት
        ext = filename.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            file_type = 'image'
        elif ext in ['mp4', 'webm', 'ogg']:
            file_type = 'video'
        elif ext in ['mp3', 'wav', 'ogg']:
            file_type = 'audio'

    new_post = Post(title=title, content=content, file_path=file_path, file_type=file_type)
    db.session.add(new_post)
    db.session.commit()
    flash("አዲስ መረጃ በተሳካ ሁኔታ ተለጥፏል!")
    return redirect(url_for('admin_dashboard'))

# ❌ ፖስት መሰረዣ መስመር
@app.route('/admin/post/delete/<int:id>')
def delete_post(id):
    post_to_delete = Post.query.get_or_404(id)
    # ፋይል ካለው ከስልኩ/ኮምፒውተሩ ላይም ያጠፋዋል
    if post_to_delete.file_path:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], post_to_delete.file_path.split('/')[-1])
        if os.path.exists(full_path):
            os.remove(full_path)
            
    db.session.delete(post_to_delete)
    db.session.commit()
    flash("መረጃው ሙሉ በሙሉ ተሰርዟል!")
    return redirect(url_for('admin_dashboard'))
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash("በተሳካ ሁኔታ ወጥተዋል!")
    return redirect(url_for('admin_login'))
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
