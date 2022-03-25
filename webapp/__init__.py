from datetime import date
from werkzeug.security import generate_password_hash
from flask import Flask, redirect, render_template, flash, url_for
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from news_parser.test_parser import result_news
import webapp.db as db
from webapp.forms import LoginForm, RegistrationForm, ProfileForm, MeetingForm
from webapp.users import add_user, add_profile, join_profile, join_meets, update_profile, add_meeting, paginate
from webapp.models import User, UserProfile, GameMeeting
from webapp.config import GAMES_PER_PAGE
from math import ceil

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Для доступа на эта страницу необходимо авторизоваться!'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @app.errorhandler(500)
    def server_error():
        title = 'Ошибка получения данных'
        return render_template('server_error.html', page_title=title), 500

    @app.route('/')
    def index():
        title = 'Поиск напарников для настольных игр'
        return render_template('index.html', page_title=title, list_news=result_news)

    @app.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        title = 'Авторизация'
        login_form = LoginForm()
        return render_template('login.html', page_title=title, form=login_form)

    @app.route('/process-login', methods=['POST'])
    def process_login():
        form = LoginForm()

        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash('Успешный вход')
                return redirect(url_for('index'))

        flash('Неправильное имя пользователя или пароль')
        return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/registration', methods=['POST', 'GET'])
    def registration():
        """
        При GET запросе возвращает страницу для регистрации.
        При POST запросе, в случае успешной валидации сохраняет
        нового пользователя в БД.
        """
        title = 'Регистрация'
        registration_form = RegistrationForm()

        if registration_form.validate_on_submit():
            hash_pass = generate_password_hash(
                registration_form['password'].data
            )
            new_user = User(
                username=registration_form['username'].data,
                password=hash_pass,
                email=registration_form['email'].data,
                role='1'
                )

            if add_user(new_user):
                flash('Вы успешно зарегистрировались!')
                return redirect(url_for('login'))

            flash('Ошибка регистрации, попробуйте повторить позже.')

        return render_template(
            'registration.html',
            page_title=title,
            form=registration_form
        )

    
    @app.route('/profile')
    @login_required
    def profile():
        title = f'Профиль {current_user.username}'
        profile_data = join_profile(current_user.id)
        meets_data = join_meets(current_user.id)
        return render_template(
            'profile.html',
            page_title=title,
            profile_data=profile_data,
            meets_data=meets_data
        )

    @app.route('/edit_profile')
    @login_required
    def edit_profile():
        title = f'Профиль {current_user.username}'
        profile_data = join_profile(current_user.id)
        profile_form = ProfileForm()
        return render_template(
            'edit_profile.html',
            page_title=title,
            form=profile_form,
            profile_data=profile_data
        )

    @app.route('/submit_profile', methods=['POST', 'GET'])
    def submit_profile():
        form = ProfileForm()

#        if form.validate_on_submit():
        if bool(UserProfile.query.filter_by(owner_id=current_user.id).first()):
            update_profile(form, current_user)
            flash('Личные данные успешно сохранены!')
            return redirect(url_for('profile'))
        new_profile = UserProfile(
            owner_id=current_user.id,
            name=form['name'].data,
            surname=form['surname'].data,
            country=form['country'].data,
            city=form['city'].data,
            favorite_games=form['favorite_games'].data,
            desired_games=form['desired_games'].data,
            about_user=form['about_user'].data
        )

        #  email_for_user = User()
        add_profile(new_profile)
        flash('Личные данные успешно сохранены!')
        return redirect(url_for('profile'))

   
    @app.route('/create_meeting', methods=['POST', 'GET'])
    @login_required
    def create_meeting():
        """
        При GET запросе возвращает страницу для создания встречи.
        При POST запросе, в случае успешной валидации сохраняет
        новую встречу в БД.
        """
        title = 'Создание встречи'
        meeting_form = MeetingForm()

        if meeting_form.validate_on_submit():
            new_meeting = GameMeeting(
                game_name=meeting_form['game_name'].data,
                owner_id=current_user.id,
                create_date=date.today(),
                number_of_players=meeting_form['number_of_players'].data,
                meeting_place=meeting_form['meeting_place'].data,
                meeting_date_time = f"{meeting_form['date_meeting'].data} {meeting_form['time_meeting'].data}",
                description=meeting_form['description'].data
                )

            if add_meeting(new_meeting):
                flash('Вы успешно создали встречу!')
                return redirect(url_for('index'))

            flash('Ошибка создания встречи, попробуйте повторить позже.')
            return redirect(url_for('server_error')) # УДАЛИТЬ

        return render_template(
            'create_meeting.html',
            page_title=title,
            form=meeting_form
        )

    @app.route('/meets', methods=['POST', 'GET'])
    @app.route('/meets/<int:page>', methods=['POST', 'GET'])
    @login_required 
    def meets(page=1):
        title = 'LFG'
        with db.db_session() as session:
            query = session.query(GameMeeting).order_by(GameMeeting.meeting_date_time.asc())
            meets_list = paginate(query, page, GAMES_PER_PAGE).all()
            last_page = ceil(session.query(GameMeeting).count()/GAMES_PER_PAGE)
        return render_template('meets.html', meets_list=meets_list, page_title=title, current_page=page, last_page=last_page)
        
    return app
