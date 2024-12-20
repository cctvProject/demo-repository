from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file, jsonify, g
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from fpdf import FPDF
from PIL import Image
import base64
import io
import easyocr
import pandas as pd
import os
import logging

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/cctv_db?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# 로깅 설정
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# 전역 카메라 객체
camera = None

# 에러 핸들러
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {str(e)}")
    return render_template("error.html", error=str(e)), 500
# -------------------------------

# 관리자 세션 유효성 검증 함수
# -------------------------------
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('role') != 'admin':
            flash("관리자 권한이 필요합니다.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function
# -------------------------------

# 데이터베이스 모델
# -------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), default='pending', nullable=False)

    reports = relationship('Report', backref='user', lazy=True)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    entry_count = db.Column(db.Integer, default=0)
    exit_count = db.Column(db.Integer, default=0)
    current_parking_count = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    total_fee = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user_name = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fee_per_10_minutes = db.Column(db.Integer, nullable=False, default=100)
    total_parking_slots = db.Column(db.Integer, nullable=False, default=50)
    total_floors = db.Column(db.Integer, nullable=False, default=5)

class Recognition(db.Model):
    __tablename__ = 'recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)
    entry_exit_input = db.Column(db.String(50), nullable=False, default='unknown')
    vehicle_type = db.Column(db.String(50), nullable=False, default='normal')

class Inquiry(db.Model):
    __tablename__ = 'inquiry'
    id = db.Column(db.Integer, primary_key=True)  # 고유 ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 작성자 ID (User 테이블 참조)
    message = db.Column(db.Text, nullable=False)  # 문의 내용
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 작성 시간

    user = db.relationship('User', backref='inquiries')  # User와 관계 설정
    
# ORM모델 직접 사용
allowed_categories = {
    'entry': {'entry_exit_input': 'entry', 'vehicle_type': None},
    'exit': {'entry_exit_input': 'exit', 'vehicle_type': None},
    'light_vehicle': {'entry_exit_input': None, 'vehicle_type': 'light'},
    'disabled_vehicle': {'entry_exit_input': None, 'vehicle_type': 'disabled'},
    'illegal_parking': {'entry_exit_input': None, 'vehicle_type': 'illegal'},
}

def get_category_data(category):
    """
    주어진 카테고리에 따라 Recognition 데이터를 필터링합니다.
    """
    allowed_categories = {
        'entry': {'entry_exit_input': 'entry', 'vehicle_type': None},
        'exit': {'entry_exit_input': 'exit', 'vehicle_type': None},
        'light_vehicle': {'entry_exit_input': None, 'vehicle_type': 'light'},
        'disabled_vehicle': {'entry_exit_input': None, 'vehicle_type': 'disabled'},
        'illegal_parking': {'entry_exit_input': None, 'vehicle_type': 'illegal'},
    }

    if category not in allowed_categories:
        raise ValueError("Invalid category")

    filters = allowed_categories[category]
    query = Recognition.query

    if filters['entry_exit_input']:
        query = query.filter_by(entry_exit_input=filters['entry_exit_input'])
    if filters['vehicle_type']:
        query = query.filter_by(vehicle_type=filters['vehicle_type'])

    return query.order_by(Recognition.recognition_time.desc()).all()


# -------------------------------

# 로그인 관련 함수
# -------------------------------
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash("로그인이 필요합니다.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.info("로그인 시도")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user.role
            flash("로그인 성공", "success")
            return redirect(url_for('home'))
        else:
            app.logger.warning(f"로그인 실패 - 사용자: {username}")
            flash("아이디나 비밀번호가 잘못되었습니다.", "danger")
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        phone = request.form['phone']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, email=email, name=name, phone=phone)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('회원가입 성공!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'오류 발생: {e}', 'danger')

    return render_template('signup.html')
# -------------------------------

# 데이터 필터링
# -------------------------------
@app.route('/recognition-data', methods=['GET'])
@login_required
def get_recognition_data():
    recognition_type = request.args.get('type')  # 'entry' 또는 'exit'
    vehicle_type = request.args.get('vehicle_type')  # 'light', 'disabled', 'illegal', 'normal'

    query = Recognition.query
    if recognition_type:
        query = query.filter_by(entry_exit_input=recognition_type)
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)

    data = query.order_by(Recognition.recognition_time.desc()).all()
    return render_template('recognition_list.html', data=data)
# -------------------------------

# 주요 라우트
# -------------------------------
@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/search')
@login_required
def search():
    data = {
        'entry': Recognition.query.filter_by(entry_exit_input='entry').order_by(Recognition.recognition_time.desc()).all(),
        'exit': Recognition.query.filter_by(entry_exit_input='exit').order_by(Recognition.recognition_time.desc()).all(),
        'light_vehicle': Recognition.query.filter_by(vehicle_type='light').order_by(Recognition.recognition_time.desc()).all(),
        'disabled_vehicle': Recognition.query.filter_by(vehicle_type='disabled').order_by(Recognition.recognition_time.desc()).all(),
        'illegal_parking': Recognition.query.filter_by(vehicle_type='illegal').order_by(Recognition.recognition_time.desc()).all(),
    }

    return render_template('search.html', data=data)

# 전역 OCR Reader 객체 생성
ocr_reader = easyocr.Reader(['en', 'ko'])

@app.route('/capture-image', methods=['POST'])
def capture_image():
    data = request.get_json()
    if not data or 'image_data' not in data or 'category' not in data:
        return jsonify({"status": "error", "error": "Invalid input data"}), 400

    # 카테고리 조건 설정
    category_models = {
        'entry': {'entry_exit_input': 'entry', 'vehicle_type': None},
        'exit': {'entry_exit_input': 'exit', 'vehicle_type': None},
        'light_vehicle': {'entry_exit_input': None, 'vehicle_type': 'light'},
        'disabled_vehicle': {'entry_exit_input': None, 'vehicle_type': 'disabled'},
        'illegal_parking': {'entry_exit_input': None, 'vehicle_type': 'illegal'}
    }

    category = data.get('category')
    if category not in category_models:
        return jsonify({"status": "error", "error": "Invalid category"}), 400

    # 카테고리별 조건 가져오기
    model_conditions = category_models[category]

    # 이미지 데이터 처리
    image_data = data['image_data'].split(",")[1]
    decoded_image = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(decoded_image))

    # 현재 시간
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 이미지 저장 폴더 설정: 카테고리 구조
    save_image_folder = os.path.join("static", "captured_images", category)
    os.makedirs(save_image_folder, exist_ok=True)
    
    # 이미지 파일 이름 설정
    image_filename = f"{timestamp}.jpg"  # 시간만 파일명으로 사용
    image_path = os.path.join(save_image_folder, image_filename)
    image.save(image_path)
    # 데이터베이스에 저장할 경로
    image_db_path = f"captured_images/{category}/{image_filename}"
    # 로그 추가
    app.logger.info(f"저장된 이미지 경로: {image_path}")

    # OCR 처리
    try:
        ocr_results = ocr_reader.readtext(image_path)
        vehicle_number = ocr_results[0][1] if ocr_results else "Unknown"
    except Exception as e:
        app.logger.error(f"OCR 처리 중 오류: {str(e)}")
        vehicle_number = "Unknown"
        
    # 데이터베이스 저장
    new_record = Recognition(
        vehicle_number=vehicle_number,  # OCR 결과 저장
        phone_number=None,
        recognition_time=datetime.now(),
        image_path=image_db_path,  # 데이터베이스 경로에 카테고리 기반 저장
        entry_exit_input=model_conditions['entry_exit_input'] if model_conditions['entry_exit_input'] else 'unknown',
        vehicle_type=model_conditions['vehicle_type'] if model_conditions['vehicle_type'] else 'normal'
    )

    db.session.add(new_record)
    try:
        db.session.commit()
        app.logger.info("데이터베이스에 이미지 경로 및 OCR 결과 저장 완료")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"데이터베이스 저장 중 오류: {str(e)}")
        return jsonify({"status": "error", "error": "Failed to save record to database"}), 500

    return jsonify({
        "status": "success",
        "ocr_text": vehicle_number,  # OCR 결과 반환
        "image_path": image_db_path  # 저장된 이미지 경로 반환
    })


# -------------------------------

# 카테고리별 비디오 인식 라우트
# -------------------------------

@app.route('/<category>-recognition', methods=['GET'])
@login_required
def video_recognition(category):
    # 카테고리별 정보 매핑
    categories = {
        'entry': {
            'title': '입차 인식',
            'video_feed': 'entry_video_feed',
            'list_page': 'entry_recognition_list',
            'button_text': '입차 리스트'
        },
        'exit': {
            'title': '출차 인식',
            'video_feed': 'exit_video_feed',
            'list_page': 'exit_recognition_list',
            'button_text': '출차 리스트'
        },
        'light-vehicle': {
            'title': '경차 인식',
            'video_feed': 'light_vehicle_video_feed',
            'list_page': 'light_vehicle_recognition_list',
            'button_text': '경차 리스트'
        },
        'disabled-vehicle': {
            'title': '장애인 차량 인식',
            'video_feed': 'disabled_vehicle_video_feed',
            'list_page': 'disabled_vehicle_recognition_list',
            'button_text': '장애인 차량 리스트'
        },
        'illegal-parking': {
            'title': '불법 주차 인식',
            'video_feed': 'illegal_parking_video_feed',
            'list_page': 'illegal_parking_recognition_list',
            'button_text': '불법 주차 리스트'
        },
    }

    # 유효한 카테고리 확인
    if category not in categories:
        flash("잘못된 카테고리 요청입니다.", "danger")
        return redirect(url_for('home'))

    # 카테고리 데이터 전달
    data = categories[category]
    return render_template(
        'video_recognition.html',
        title=data['title'],
        video_feed=data['video_feed'],
        list_page=data['list_page'],
        button_text=data['button_text'],
        category=category
    )
# -------------------------------

# 보안 관련 라우트 및 기능
# -------------------------------

@app.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    # 관리자 권한 확인
    if session.get('role') != 'admin':
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for('home'))

    # 모든 사용자 정보 가져오기
    users = User.query.all()
    return render_template('security.html', users=users)
# -------------------------------

# 유저 role 승인 및 삭제 라우트 및 기능
# -------------------------------

@app.route('/update-role', methods=['POST'])
@login_required
def update_role():
    if session.get('role') != 'admin':
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for('security'))

    user_id = request.form.get('user_id')
    new_role = request.form.get('new_role')

    user = User.query.get(user_id)
    if not user:
        flash("사용자를 찾을 수 없습니다.", "danger")
        return redirect(url_for('security'))

    try:
        user.role = new_role
        db.session.commit()
        flash(f"사용자 '{user.username}'의 역할이 '{new_role}'로 변경되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"역할 업데이트 중 오류 발생: {str(e)}", "danger")

    return redirect(url_for('security'))

@app.route('/delete-user', methods=['POST'])
@login_required
def delete_user():
    if session.get('role') != 'admin':
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for('security'))

    user_id = request.form.get('user_id_to_delete')
    user = User.query.get(user_id)

    if not user:
        flash("사용자를 찾을 수 없습니다.", "danger")
        return redirect(url_for('security'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"사용자 '{user.username}'가 삭제되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"사용자 삭제 중 오류 발생: {str(e)}", "danger")

    return redirect(url_for('security'))

# -------------------------------

# 문의 사항 관련 라우트 및 기능
# -------------------------------
@app.route('/inquiry_write', methods=['GET', 'POST'])
@login_required
def inquiry_write():
    app.logger.info(f"POST 요청 전에 세션 상태: {session}")

    # 역할(role) 확인
    user_role = session.get('role')
    if user_role != 'user':  # 일반 사용자만 접근 허용
        app.logger.warning("사용자 역할이 'user'가 아님")
        flash("일반 사용자만 이 기능을 사용할 수 있습니다.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        # 세션에서 username 가져오기
        username = session.get('username')
        user = User.query.filter_by(username=username).first()

        if not user:
            app.logger.warning("세션에 username이 없거나 유효하지 않음")
            flash("로그인이 필요합니다.", "danger")
            return redirect(url_for('login'))

        message = request.form.get('message', '').strip()
        if not message:
            flash("문의 내용을 입력하세요.", "warning")
            return redirect(url_for('inquiry_write'))

        # 데이터 저장
        new_inquiry = Inquiry(user_id=user.id, message=message)
        try:
            db.session.add(new_inquiry)
            db.session.commit()
            flash("문의 사항이 성공적으로 제출되었습니다!", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"문의 사항 저장 중 오류: {e}")
            flash("문의 사항 제출 중 오류가 발생했습니다.", "danger")

        app.logger.info(f"POST 요청 처리 후 세션 상태: {session}")
        return redirect(url_for('inquiry'))

    return render_template('inquiry_write.html')


@app.route('/inquiry', methods=['GET'])
@login_required
def inquiry():
    # 모든 문의 데이터 가져오기
    inquiries = Inquiry.query.join(User).add_columns(
        User.username, Inquiry.message, Inquiry.created_at
    ).all()

    # 템플릿에 데이터 전달
    return render_template('inquiry.html', inquiries=inquiries)
# -------------------------------

# 각 카테고리 별 검색 라우트 및 기능
# -------------------------------
@app.route('/search-results', methods=['GET', 'POST'])
@login_required
def search_results():
    query = None
    results = {}

    if request.method == 'POST':
        query = request.form.get('query', '').strip()

        if query and len(query) == 4 and query.isdigit():
            results = {
                '입차 인식': Recognition.query.filter(
                    Recognition.entry_exit_input == 'entry',
                    Recognition.vehicle_number.like(f'%{query}%')
                ).order_by(Recognition.recognition_time.desc()).all(),

                '출차 인식': Recognition.query.filter(
                    Recognition.entry_exit_input == 'exit',
                    Recognition.vehicle_number.like(f'%{query}%')
                ).order_by(Recognition.recognition_time.desc()).all(),

                '경차 인식': Recognition.query.filter(
                    Recognition.vehicle_type == 'light',
                    Recognition.vehicle_number.like(f'%{query}%')
                ).order_by(Recognition.recognition_time.desc()).all(),

                '장애인 차량 인식': Recognition.query.filter(
                    Recognition.vehicle_type == 'disabled',
                    Recognition.vehicle_number.like(f'%{query}%')
                ).order_by(Recognition.recognition_time.desc()).all(),

                '불법 주차 차량 인식': Recognition.query.filter(
                    Recognition.vehicle_type == 'illegal',
                    Recognition.vehicle_number.like(f'%{query}%')
                ).order_by(Recognition.recognition_time.desc()).all(),
            }

    return render_template('search_results.html', query=query, results=results)

# -------------------------------

# 기타 사항 / 카테고리 리스트 및 검색 결과 라우트
# -------------------------------
@app.route('/recognition-list/<string:category>', methods=['GET'])
@login_required
def recognition_list(category):
    # get_category_data 함수 사용
    try:
        data = get_category_data(category)
    except ValueError:
        flash("Invalid category!", "danger")
        return redirect(url_for('search'))

    # 페이지네이션 추가
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (len(data) + per_page - 1) // per_page
    paginated_data = data[(page - 1) * per_page: page * per_page]

    return render_template(
        'recognition_list.html',
        data=paginated_data,
        page=page,
        total_pages=total_pages,
        category=category
    )

# -------------------------------

# 기타 사항 / 출퇴근 목록 페이지
# -------------------------------
@app.route('/work', methods=['GET', 'POST'])
@login_required
def work():
    if request.method == 'POST':
        if 'start_time_button' in request.form:
            existing_report = Report.query.filter_by(user_name=session['username'], end_time=None).first()
            if existing_report:
                flash("이미 출근 상태입니다. 퇴근 후 다시 출근할 수 있습니다.", "danger")
            else:
                start_time = datetime.now()
                new_report = Report(
                    entry_count=0,
                    exit_count=0,
                    current_parking_count=0,
                    start_time=start_time,
                    end_time=None,
                    total_fee=0,
                    user_name=session['username']
                )
                db.session.add(new_report)
                db.session.commit()
                flash("출근 시간이 기록되었습니다!", "success")

        elif 'end_time_button' in request.form:
            end_time = datetime.now()
            report = Report.query.filter_by(user_name=session['username'], end_time=None).first()
            if report:
                report.end_time = end_time
                db.session.commit()
                flash("퇴근 시간이 기록되었습니다!", "success")
            else:
                flash("출근 기록이 없습니다.", "danger")

    page = request.args.get('page', 1, type=int)
    per_page = 10
    reports = Report.query.filter_by(user_name=session['username']).order_by(Report.start_time.desc()).paginate(page=page, per_page=per_page)
    return render_template('work.html', reports=reports)

# -------------------------------

# 기타 사항 / 리포트 작성 페이지
# -------------------------------
# 보고서 페이지 및 데이터 입력, 표시
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    user_name = session['username']
    setting = Setting.query.first()
    fee_per_10_minutes = setting.fee_per_10_minutes if setting else 100

    if request.method == 'POST':
        if 'start_time_button' in request.form:
            existing_report = Report.query.filter_by(user_name=user_name, end_time=None).first()
            if existing_report:
                flash("이미 출근 상태입니다. 퇴근 후 다시 출근하세요.", "danger")
            else:
                start_time = datetime.now()
                new_report = Report(
                    entry_count=0,
                    exit_count=0,
                    current_parking_count=0,
                    start_time=start_time,
                    end_time=None,
                    total_fee=0,
                    user_name=user_name
                )
                db.session.add(new_report)
                db.session.commit()
                flash("출근 시간이 기록되었습니다!", "success")

        elif 'end_time_button' in request.form:
            end_time = datetime.now()
            report = Report.query.filter_by(user_name=user_name, end_time=None).first()
            if report:
                report.end_time = end_time

                entry_records = get_category_data('entry')
                exit_records = get_category_data('exit')

                report.entry_count = len(entry_records)
                report.exit_count = len(exit_records)

                entry_vehicle_numbers = {record.vehicle_number for record in entry_records}
                exit_vehicle_numbers = {record.vehicle_number for record in exit_records}
                report.current_parking_count = len(entry_vehicle_numbers - exit_vehicle_numbers)

                total_parking_minutes = sum(
                    (end_time - record.recognition_time).total_seconds() // 60 for record in entry_records
                )
                report.total_fee = (total_parking_minutes // 10) * fee_per_10_minutes

                db.session.commit()
                flash("퇴근 시간이 기록되었습니다!", "success")
            else:
                flash("출근 기록이 없습니다. 출근 버튼을 눌러주세요.", "danger")

    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(user_name=user_name).order_by(Report.start_time.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template('report.html', reports=reports)

# -------------------------------

# 기타 사항 / 알람 페이지
# -------------------------------
@app.route('/alerts', methods=['GET'])
@login_required
def alerts():
    now = datetime.utcnow()
    three_hours_ago = now - timedelta(hours=3)

    query = Recognition.query.filter(
        Recognition.recognition_time >= three_hours_ago
    ).order_by(Recognition.recognition_time.desc())

    page = request.args.get('page', 1, type=int)
    paginated_data = query.paginate(page=page, per_page=10, error_out=False)

    return render_template(
        'alerts.html',
        all_data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )
# -------------------------------

# 기타 사항 / 환경 설정
# -------------------------------
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    setting = Setting.query.first()
    if request.method == 'POST':
        fee = request.form.get('fee_per_10_minutes', type=int)
        total_slots = request.form.get('total_parking_slots', type=int)
        total_floors = request.form.get('total_floors', type=int)

        if fee <= 0 or total_slots <= 0 or total_floors <= 0:
            flash("설정 값은 0보다 커야 합니다.", "danger")
            return redirect(url_for('settings'))

        if setting:
            setting.fee_per_10_minutes = fee
            setting.total_parking_slots = total_slots
            setting.total_floors = total_floors
        else:
            setting = Setting(fee_per_10_minutes=fee, total_parking_slots=total_slots, total_floors=total_floors)
            db.session.add(setting)
        db.session.commit()
        flash("환경 설정이 성공적으로 업데이트되었습니다!", "success")
    return render_template('settings.html', setting=setting)
# -------------------------------

# 기타 사항 / PDF, EXCEL
# -------------------------------
@app.route('/export/<string:category>/<string:file_format>', methods=['GET'])
@login_required
def export_category_data(category, file_format):
    data = get_category_data(category)
    df = pd.DataFrame([{
        '차량 번호': record.vehicle_number,
        '핸드폰 번호': record.phone_number,
        '인식 시간': record.recognition_time.strftime('%Y-%m-%d %H:%M:%S') if record.recognition_time else None,
        '이미지 경로': record.image_path
    } for record in data])

    folder_path = os.path.join('static', category)
    os.makedirs(folder_path, exist_ok=True)

    if file_format == 'pdf':
        file_path = os.path.join(folder_path, f'{category}_data.pdf')
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font('Arial', size=12)
        pdf.cell(200, 10, txt=f"{category.capitalize()} Data", ln=True, align='C')
        for _, row in df.iterrows():
            pdf.cell(200, 10, txt=str(row.to_dict()), ln=True)

        pdf.output(file_path)
        return send_file(file_path, as_attachment=True)

    elif file_format == 'excel':
        file_path = os.path.join(folder_path, f'{category}_data.xlsx')
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    flash("유효하지 않은 파일 형식입니다.", "danger")
    return redirect(url_for('search'))
# -------------------------------

# 관리자 이메일 가져오는 라우트
# -------------------------------
@app.before_request
def inject_admin_email():
    # 관리자 계정을 검색
    admin_user = User.query.filter_by(role='admin').first()
    
    # 관리자 이메일을 g 객체에 저장
    g.admin_email = admin_user.email if admin_user else "관리자 이메일 없음"
# -------------------------------

# 서버 실행
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
