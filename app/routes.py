# app/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, abort
from flask_login import login_user, current_user, logout_user, login_required
from .models import User, GeneratedText, EditedVideo, CreatedGraphic
from . import db
from .utils.text_generation import generate_text
from .utils.video_editing import edit_video
from .utils.graphic_creation import create_graphic
from .utils.trend_analysis import get_trends
from .forms import RegistrationForm, LoginForm, GenerateTextForm, EditVideoForm, CreateGraphicForm
from werkzeug.utils import secure_filename
import os
import jwt
import datetime
from functools import wraps
import io

# Blueprint for main routes
main = Blueprint('main', __name__)

# JWT Token Protection (if needed)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'error': 'Token is missing!'}), 403

        try:
            # Decode the token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user = User.query.filter_by(id=data['id']).first()
            if not user:
                return jsonify({'error': 'User not found!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 403

        return f(user, *args, **kwargs)

    return decorated

# Authentication Routes

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        # Create a new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

# Dashboard Route
@main.route('/')
@login_required
def index():
    generated_text_count = GeneratedText.query.filter_by(user_id=current_user.id).count()
    edited_video_count = EditedVideo.query.filter_by(user_id=current_user.id).count()
    created_graphic_count = CreatedGraphic.query.filter_by(user_id=current_user.id).count()
    trends_count = 0  # Update this if you have a trends counter

    # Example data for chart (replace with real data if available)
    labels = ['January', 'February', 'March', 'April', 'May']
    data = [
        GeneratedText.query.filter(
            GeneratedText.user_id == current_user.id,
            db.extract('month', GeneratedText.timestamp) == 1
        ).count(),
        GeneratedText.query.filter(
            GeneratedText.user_id == current_user.id,
            db.extract('month', GeneratedText.timestamp) == 2
        ).count(),
        GeneratedText.query.filter(
            GeneratedText.user_id == current_user.id,
            db.extract('month', GeneratedText.timestamp) == 3
        ).count(),
        GeneratedText.query.filter(
            GeneratedText.user_id == current_user.id,
            db.extract('month', GeneratedText.timestamp) == 4
        ).count(),
        GeneratedText.query.filter(
            GeneratedText.user_id == current_user.id,
            db.extract('month', GeneratedText.timestamp) == 5
        ).count(),
    ]

    return render_template(
        'index.html',
        generated_text_count=generated_text_count,
        edited_video_count=edited_video_count,
        created_graphic_count=created_graphic_count,
        trends_count=trends_count,
        chart_labels=labels,
        chart_data=data
    )

# Generate Text Route
@main.route('/generate-text', methods=['GET', 'POST'])
@login_required
def generate_text_route():
    form = GenerateTextForm()
    if form.validate_on_submit():
        keywords = form.keywords.data.strip()
        tone = form.tone.data
        length = form.length.data
        temperature = form.temperature.data
        max_tokens = form.max_tokens.data

        if not keywords:
            flash('Please enter keywords.', 'danger')
            return redirect(url_for('main.generate_text_route'))

        generated = generate_text(keywords, tone, length, temperature, max_tokens)

        if generated is None:
            flash('Error generating text.', 'danger')
            return redirect(url_for('main.generate_text_route'))

        # Save the generated text
        new_text = GeneratedText(
            user_id=current_user.id,
            keywords=keywords,
            tone=tone,
            length=length,
            temperature=temperature,
            max_tokens=max_tokens,
            content=generated
        )
        db.session.add(new_text)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database commit error: {e}")
            flash('Error saving text to the database.', 'danger')
            return redirect(url_for('main.generate_text_route'))

        flash('Text successfully generated and saved.', 'success')
        return render_template(
            'generate_text.html',
            form=form,
            generated_text=generated,
            new_text=new_text  # Pass the object to use its ID
        )

    return render_template('generate_text.html', form=form)

# Edit Video Route
@main.route('/edit-video', methods=['GET', 'POST'])
@login_required
def edit_video_route():
    form = EditVideoForm()
    if form.validate_on_submit():
        file = form.video.data
        if file:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            upload_path = os.path.join(upload_dir, filename)
            file.save(upload_path)

            # Editing parameters (can be expanded via the form)
            edited_filename = edit_video(upload_path)

            if edited_filename:
                # Save information about the edited video
                new_video = EditedVideo(
                    user_id=current_user.id,
                    original_filename=filename,
                    edited_filename=edited_filename
                )
                db.session.add(new_video)
                db.session.commit()

                flash('Video successfully edited.', 'success')
                return render_template('edit_video.html', form=form, edited_video=new_video)
            else:
                flash('Error editing video.', 'danger')
                return redirect(url_for('main.edit_video_route'))

    return render_template('edit_video.html', form=form)

# Create Graphic Route
@main.route('/create-graphic', methods=['GET', 'POST'])
@login_required
def create_graphic_route():
    form = CreateGraphicForm()
    if not form.template.choices:
        # Populate template choices from the graphics templates directory
        templates_dir = os.path.join(current_app.root_path, 'static', 'templates_graphics')
        if os.path.exists(templates_dir):
            templates = [f for f in os.listdir(templates_dir) if os.path.isfile(os.path.join(templates_dir, f))]
            form.template.choices = [(template, template) for template in templates]
        else:
            form.template.choices = []
            flash('Graphics templates directory not found.', 'danger')

    if form.validate_on_submit():
        template = form.template.data
        text = form.text.data.strip()

        if not template or not text:
            flash('Please select a template and enter text.', 'danger')
            return redirect(url_for('main.create_graphic_route'))

        graphic_filename = create_graphic(template, text)

        if graphic_filename:
            # Save information about the created graphic
            new_graphic = CreatedGraphic(
                user_id=current_user.id,
                template=template,
                text=text,
                output_filename=graphic_filename
            )
            db.session.add(new_graphic)
            db.session.commit()

            flash('Graphic successfully created and saved.', 'success')
            return render_template('create_graphic.html', form=form, graphic=new_graphic)
        else:
            flash('Error creating graphic.', 'danger')
            return redirect(url_for('main.create_graphic_route'))

    return render_template('create_graphic.html', form=form)

# Trends Analysis Route
@main.route('/trends', methods=['GET', 'POST'])
@login_required
def trends_route():
    trends = None
    keyword = None
    if request.method == 'POST':
        keyword = request.form.get('keyword').strip()
        timeframe = request.form.get('timeframe', 'today 12-m')
        if keyword:
            trends = get_trends(keyword, timeframe)
            if not trends:
                flash('Failed to retrieve trend data.', 'danger')
            else:
                flash('Trend data successfully retrieved.', 'success')
        else:
            flash('Please enter a keyword for trend analysis.', 'danger')

    return render_template('trends.html', trends=trends, keyword=keyword)

# Helper function to check allowed file extensions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Routes for Viewing and Managing Generated Content

@main.route('/my-texts')
@login_required
def my_texts():
    page = request.args.get('page', 1, type=int)
    texts = GeneratedText.query.filter_by(user_id=current_user.id).order_by(GeneratedText.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('my_texts.html', texts=texts)

@main.route('/my-videos')
@login_required
def my_videos():
    page = request.args.get('page', 1, type=int)
    videos = EditedVideo.query.filter_by(user_id=current_user.id).order_by(EditedVideo.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('my_videos.html', videos=videos)

@main.route('/my-graphics')
@login_required
def my_graphics():
    page = request.args.get('page', 1, type=int)
    graphics = CreatedGraphic.query.filter_by(user_id=current_user.id).order_by(CreatedGraphic.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('my_graphics.html', graphics=graphics)

# Export Generated Text
@main.route('/export-text/<int:text_id>')
@login_required
def export_text(text_id):
    text = GeneratedText.query.get_or_404(text_id)
    if text.user_id != current_user.id:
        abort(403)

    return send_file(
        io.BytesIO(text.content.encode()),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"{text.keywords}.txt"
    )

# Export Video
@main.route('/export-video/<int:video_id>')
@login_required
def export_video(video_id):
    video = EditedVideo.query.get_or_404(video_id)
    if video.user_id != current_user.id:
        abort(403)

    video_path = os.path.join(current_app.root_path, 'static', 'edited_videos', video.edited_filename)
    if not os.path.exists(video_path):
        flash('Edited video file not found.', 'danger')
        return redirect(url_for('main.my_videos'))

    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name=video.edited_filename
    )

# Export Graphic
@main.route('/export-graphic/<int:graphic_id>')
@login_required
def export_graphic(graphic_id):
    graphic = CreatedGraphic.query.get_or_404(graphic_id)
    if graphic.user_id != current_user.id:
        abort(403)

    graphic_path = os.path.join(current_app.root_path, 'static', 'graphics', graphic.output_filename)
    if not os.path.exists(graphic_path):
        flash('Graphic file not found.', 'danger')
        return redirect(url_for('main.my_graphics'))

    return send_file(
        graphic_path,
        mimetype='image/png',
        as_attachment=True,
        download_name=graphic.output_filename
    )

# Delete Generated Text
@main.route('/delete-text/<int:text_id>', methods=['POST'])
@login_required
def delete_text(text_id):
    text = GeneratedText.query.get_or_404(text_id)
    if text.user_id != current_user.id:
        abort(403)

    db.session.delete(text)
    db.session.commit()

    flash('Text successfully deleted.', 'success')
    return redirect(url_for('main.my_texts'))

# Delete Edited Video
@main.route('/delete-video/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    video = EditedVideo.query.get_or_404(video_id)
    if video.user_id != current_user.id:
        abort(403)

    # Delete video files from the filesystem
    original_path = os.path.join(current_app.root_path, 'static', 'uploads', video.original_filename)
    edited_path = os.path.join(current_app.root_path, 'static', 'edited_videos', video.edited_filename)

    try:
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(edited_path):
            os.remove(edited_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting video files: {e}")
        flash('Error deleting video files.', 'danger')
        return redirect(url_for('main.my_videos'))

    db.session.delete(video)
    db.session.commit()

    flash('Video successfully deleted.', 'success')
    return redirect(url_for('main.my_videos'))

# Delete Created Graphic
@main.route('/delete-graphic/<int:graphic_id>', methods=['POST'])
@login_required
def delete_graphic(graphic_id):
    graphic = CreatedGraphic.query.get_or_404(graphic_id)
    if graphic.user_id != current_user.id:
        abort(403)

    # Delete graphic file from the filesystem
    graphic_path = os.path.join(current_app.root_path, 'static', 'graphics', graphic.output_filename)

    try:
        if os.path.exists(graphic_path):
            os.remove(graphic_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting graphic file: {e}")
        flash('Error deleting graphic file.', 'danger')
        return redirect(url_for('main.my_graphics'))

    db.session.delete(graphic)
    db.session.commit()

    flash('Graphic successfully deleted.', 'success')
    return redirect(url_for('main.my_graphics'))

# Add other routes as needed
