from . import auth
from .forms import LoginForm, RegisterForm, ChangePasswordForm
from flask import request, render_template, url_for, redirect, flash
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, Team, db
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_

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

@auth.route('/profile')
def profile():
    
    if not current_user.is_authenticated:
        flash("Sign in to view your profile.", "warning")
        return redirect(url_for('auth.login'))
    else:
        return render_template('profile.html')
    
@auth.route('/change_password', methods=['GET', 'POST'])
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

@auth.route('/update_profile')
def update_profile():
    return render_template('update_profile.html')

@auth.route('/notifications')
def notifications():
    return render_template('notifications.html')