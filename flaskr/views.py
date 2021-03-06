from flask import(
    Blueprint, abort, request, render_template, redirect, url_for, flash
)
from flask_login import login_user, login_required, logout_user
from flaskr.models import(
    User, PasswordResetToken
)
from flaskr import db

from flaskr.forms import(
    LoginForm, RegisterForm, RegisterPasswordForm
)

bp = Blueprint('app', __name__, url_prefix='')


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('app.home'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.select_user_by_email(form.email.data)
        if user and user.is_active and user.validate_password(form.password.data):
            login_user(user, remember=True)
            next = request.args.get('next')
            if not next:
                next = url_for('app.home')
            return redirect(next)
        elif not user:
            flash('存在しないユーザーです')
        elif not user.is_active:
            flash('無効なユーザーです')
        elif not user.validate_password(form.password.data):
            flash('メールアドレスとパスワードの組み合わせが誤っています')
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        with db.session.begin(subtransactions=True):
            user.create_new_user()
        db.session.commit()
        token = ''
        with db.session.begin(subtransactions=True):
            token = PasswordResetToken.publish_token(user)
        db.session.commit()
        print(f'パスワード設定用URL:http://127.0.0.1:5000/reset_password/{token}')
        return redirect(url_for('app.login'))
    return render_template('register.html', form=form)


@bp.route('reset_password/<uuid:token>', methods=['GET', 'POST'])
def reset_password(token):
    form = RegisterPasswordForm(request.form)
    reset_user_id = PasswordResetToken.get_user_id_by_token(token)
    if not reset_user_id:
        abort(500)
    if request.method == 'POST' and form.validate:
