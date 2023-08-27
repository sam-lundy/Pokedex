from . import auth
from .forms import LoginForm, RegisterForm, ChangePasswordForm, UpdateProfilePictureForm, UpdateProfileForm
from flask import request, render_template, url_for, redirect, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, Team, db
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_
from app.utils import save_picture
import os


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        login_input = form.user_or_email.data.strip().lower()
        password = form.password.data

        #using the or_ feature of sqlalchemy, can query based on email or username
        queried_user = User.query.filter(or_(User.email == login_input, User.username == login_input)).first()

        if queried_user and check_password_hash(queried_user.password, password):
            login_user(queried_user)
            flash(f"{queried_user.username} logged in.", "success")

            #redirects to the page user was on before login, if exists
            next_page = request.args.get('next', url_for('main.home'))
            return redirect(next_page)
        
        else:
            flash("Invalid email/username or password.", "danger")
            return redirect(url_for('auth.login'))
        
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        name = form.name.data
        email = form.email.data.strip().lower()
        username = form.username.data.strip().lower()
        password = form.password.data

        #first() stops matching at first result
        existing_user_or_email = User.query.filter(
            or_(User.email == email, User.username == username)).first()

        if existing_user_or_email:
            flash("User already exists!", "danger")
            return render_template('register.html', form=form)

        if form.validate_on_submit():
            new_user = User(name, email, username, password)

            try:
                db.session.add(new_user)
                db.session.commit()

                new_team = Team(user_id=new_user.id)
                db.session.add(new_team)
                db.session.commit()

            #Error handling
            except Exception as e:
                db.session.rollback()
                print(f"Error: {e}")
                flash("There was an error registering your account. Please try again.", "danger")
                return redirect(url_for('auth.register'))
            
            else:
                flash(f"Thank you for registering, {new_user.username}!", "success")
                return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth.route('/profile', methods=['GET', 'POST'])
def profile():
    pic_form = UpdateProfilePictureForm()
    bio_form = UpdateProfileForm()

    wins = current_user.get_wins()
    losses = current_user.get_losses()
    draws = current_user.get_draws()
    
    if not current_user.is_authenticated:
        flash("Sign in to view your profile.", "warning")
        return redirect(url_for('auth.login'))
    
    print(current_user.bio)

    if not current_user.bio:
        current_user.bio = ""

    if bio_form.validate_on_submit():
        current_user.bio = bio_form.bio.data
        db.session.commit()
        flash("Your bio has been updated.", "info")
        return redirect(url_for('auth.profile'))
    else:
        return render_template('profile.html', pic_form=pic_form, bio_form=bio_form, wins=wins, losses=losses, draws=draws)
    

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash('Current password is incorrect!', 'danger')
            return redirect(url_for('auth.change_password'))

        # Check if the new password and its confirmation match
        if form.new_password.data != form.new_password_conf.data:
            flash('New password and its confirmation do not match!', 'danger')
            return redirect(url_for('auth.change_password'))

        # Update the user's password
        current_user.password = generate_password_hash(form.new_password.data, method='sha256')
        db.session.commit()

        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('change_pass.html', form=form)


@auth.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')


@auth.route('/update-profile-picture', methods=['POST'])
@login_required
def update_profile_picture():
    form = UpdateProfilePictureForm()

    if form.validate_on_submit():
        
        file = form.picture.data

        if not file or file.filename == '':
            flash('Please select a file.', 'warning')
            return redirect(url_for('auth.profile'))
        
        picture_file = save_picture(file)
        current_user.profile_picture = picture_file
        db.session.commit()
        flash('Your profile picture has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return redirect(url_for('auth.profile'))


@auth.route('/delete-profile-picture', methods=['POST'])
@login_required
def delete_profile_picture():
    # Default profile picture check, so we don't delete it.
    if current_user.profile_picture != 'default.jpg':
        # Create a path to the image
        picture_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.profile_picture)
        
        # Check if the image exists and then delete it
        if os.path.exists(picture_path):
            os.remove(picture_path)

        # Reset the image to the default one
        current_user.profile_picture = 'default_user_icon.png'
        db.session.commit()
        flash("Your profile picture has been deleted!', 'success")
    else:
        flash("You don't have a profile picture set.', 'info")

    return redirect(url_for('auth.profile'))
