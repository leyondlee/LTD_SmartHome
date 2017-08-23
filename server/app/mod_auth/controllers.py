from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user
from app.mod_auth.models import User
from app.mod_auth.forms import LoginForm, ChangePasswordForm
from app.common import login_exempt
import json

mod_auth = Blueprint('auth', __name__, url_prefix='/auth')

@mod_auth.route('/login', methods=['GET', 'POST'])
@login_exempt
def login():
	form = LoginForm(request.form)
	error = None
	
	if form.validate_on_submit():
		username = request.form['username']
		password = request.form['password']
		
		if 'rememberme' in request.form:
			rememberme = request.form['rememberme']
		else:
			rememberme = False
		
		user = User.query.filter_by(username=username).first()
		if user and user.check_password(password):
			login_user(user,remember=rememberme)
			return redirect(url_for('main.index'))
		else:
			error = 'Invalid username or password.'
	
	return render_template('auth/login.html', form=form, error=error)
	
@mod_auth.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('auth.login'))
	
@mod_auth.route('/status')
def status():
	return json.dumps({'Authenticated': True})

@mod_auth.route('/account', methods=['GET', 'POST'])
def account():
	form = ChangePasswordForm(request.form)
	error = None
	success = None
	
	if form.validate_on_submit():
		currentpassword = request.form['currentpassword']
		newpassword = request.form['newpassword']
		confirmpassword = request.form['confirmpassword']
		
		user = current_user
		if user.check_password(currentpassword):
			user.set_password(newpassword)
			success = 'Password has been changed.'
		else:
			error = 'Current password is incorrect.'
	
	templateData = {
		'apikey': current_user.apikey,
		'form': form,
		'error': error,
		'success': success
	}
	
	return render_template('auth/account.html', **templateData)
	
@mod_auth.route('/account/apikey')
def apikey():
	return json.dumps({'apikey': current_user.apikey})
	
@mod_auth.route('/account/apikey/generate')
def generateapikey():
	current_user.generateApiKey()
		
	return redirect(url_for('auth.account'))

@mod_auth.route('/account/apikey/delete')
def deleteapikey():
	current_user.deleteApiKey()
	
	return redirect(url_for('auth.account'))