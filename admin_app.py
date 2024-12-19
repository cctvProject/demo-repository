from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file, Response, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from fpdf import FPDF
from PIL import Image
import base64
import io
import cv2
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

# 로그 설정
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# 전역 카메라 객체
camera = None
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
    user_name = db.Column(db.String(80), db.ForeignKey('users.name'), nullable=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fee_per_10_minutes = db.Column(db.Integer, nullable=False, default=100)
    total_parking_slots = db.Column(db.Integer, nullable=False, default=50)
    total_floors = db.Column(db.Integer, nullable=False, default=5)

class EntryRecognition(db.Model):
    __tablename__ = 'entry_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

class ExitRecognition(db.Model):
    __tablename__ = 'exit_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

class LightVehicleRecognition(db.Model):
    __tablename__ = 'light_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

class DisabledVehicleRecognition(db.Model):
    __tablename__ = 'disabled_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

class IllegalParkingVehicleRecognition(db.Model):
    __tablename__ = 'illegal_parking_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255), nullable=True)

# -------------------------------
# 로그인 관련 함수
# -------------------------------
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user.role
            flash('로그인 성공!', 'success')
            return redirect(url_for('home'))
        else:
            flash('아이디나 비밀번호가 잘못되었습니다.', 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
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
        'entry': EntryRecognition.query.order_by(EntryRecognition.recognition_time.desc()).all(),
        'exit': ExitRecognition.query.order_by(ExitRecognition.recognition_time.desc()).all(),
        'light_vehicle': LightVehicleRecognition.query.order_by(LightVehicleRecognition.recognition_time.desc()).all(),
        'disabled_vehicle': DisabledVehicleRecognition.query.order_by(DisabledVehicleRecognition.recognition_time.desc()).all(),
        'illegal_parking': IllegalParkingVehicleRecognition.query.order_by(IllegalParkingVehicleRecognition.recognition_time.desc()).all()
    }
    return render_template('search.html', data=data)

@app.route('/capture-image', methods=['POST'])
def capture_image():
    data = request.get_json()
    if not data or 'image_data' not in data or 'category' not in data:
        return jsonify({"status": "error", "error": "Invalid input data"}), 400

    category_models = {
        'entry': EntryRecognition,
        'exit': ExitRecognition,
        'light_vehicle': LightVehicleRecognition,
        'disabled_vehicle': DisabledVehicleRecognition,
        'illegal_parking': IllegalParkingVehicleRecognition
    }

    category = data.get('category')
    if category not in category_models:
        return jsonify({"status": "error", "error": "Invalid category"}), 400

    model = category_models[category]
    image_data = data['image_data'].split(",")[1]
    decoded_image = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(decoded_image))

    # 카테고리별 폴더 생성
    save_image_folder = os.path.join("static", "captured_images", category)
    os.makedirs(save_image_folder, exist_ok=True)  # 폴더가 없으면 생성

    # 이미지 파일 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_path = os.path.join(save_image_folder, f"{category}_{timestamp}.jpg")
    image.save(image_path)

    # OCR 처리
    reader = easyocr.Reader(['en', 'ko'])
    ocr_results = reader.readtext(image_path)
    vehicle_number = ocr_results[0][1] if ocr_results else "Unknown"

    # 데이터베이스에 저장
    new_record = model(
        vehicle_number=vehicle_number,
        phone_number=None,
        recognition_time=datetime.now(),
        image_path=image_path
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        "status": "success",
        "ocr_text": vehicle_number,
        "image_path": image_path
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

@app.route('/emergencies', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # 문의 사항 처리
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # 문의 사항을 로그 파일에 기록
        app.logger.info(f"문의 사항 - 이름: {name}, 이메일: {email}, 메시지: {message}")

        flash("문의 사항이 성공적으로 접수되었습니다. 빠른 시일 내에 답변 드리겠습니다.", "success")
        return redirect(url_for('home'))

    return render_template('emergencies.html')

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
            # 각 카테고리에서 검색
            results = {
                '입차 인식': EntryRecognition.query.filter(
                    EntryRecognition.vehicle_number.like(f'%{query}%')
                ).order_by(EntryRecognition.recognition_time.desc()).all(),

                '출차 인식': ExitRecognition.query.filter(
                    ExitRecognition.vehicle_number.like(f'%{query}%')
                ).order_by(ExitRecognition.recognition_time.desc()).all(),

                '경차 인식': LightVehicleRecognition.query.filter(
                    LightVehicleRecognition.vehicle_number.like(f'%{query}%')
                ).order_by(LightVehicleRecognition.recognition_time.desc()).all(),

                '장애인 차량 인식': DisabledVehicleRecognition.query.filter(
                    DisabledVehicleRecognition.vehicle_number.like(f'%{query}%')
                ).order_by(DisabledVehicleRecognition.recognition_time.desc()).all(),

                '불법 주차 차량 인식': IllegalParkingVehicleRecognition.query.filter(
                    IllegalParkingVehicleRecognition.vehicle_number.like(f'%{query}%')
                ).order_by(IllegalParkingVehicleRecognition.recognition_time.desc()).all(),
            }

    return render_template('search_results.html', query=query, results=results)


# -------------------------------
# 기타 사항 / 카테고리 리스트 및 검색 결과 라우트
# -------------------------------

@app.route('/recognition-list/<string:category>', methods=['GET'])
@login_required
def recognition_list(category):
    # 모델 매핑
    allowed_categories = {
        'entry': EntryRecognition,
        'exit': ExitRecognition,
        'light_vehicle': LightVehicleRecognition,
        'disabled_vehicle': DisabledVehicleRecognition,
        'illegal_parking': IllegalParkingVehicleRecognition,
    }

    if category not in allowed_categories:
        flash("Invalid category!", "danger")
        return redirect(url_for('search'))

    model = allowed_categories[category]
    page = request.args.get('page', 1, type=int)
    per_page = 10
    paginated_data = model.query.order_by(model.recognition_time.desc()).paginate(page=page, per_page=per_page)

    return render_template('recognition_list.html', data=paginated_data.items, page=page, total_pages=paginated_data.pages, category=category)

# -------------------------------
# 기타 사항 / 출퇴근 목록 페이지
# -------------------------------

@app.route('/work', methods=['GET', 'POST'])
@login_required
def work():
    if request.method == 'POST':
        if 'start_time_button' in request.form:
            flash("출근 시간이 기록되었습니다!", "success")
        elif 'end_time_button' in request.form:
            flash("퇴근 시간이 기록되었습니다!", "success")
        # 데이터베이스에 저장 로직 추가

    page = request.args.get('page', 1, type=int)
    reports = Report.query.order_by(Report.start_time.desc()).paginate(page=page, per_page=10)
    return render_template('work.html', reports=reports)

# -------------------------------
# 기타 사항 / 알람 페이지
# -------------------------------

@app.route('/alerts', methods=['GET'])
@login_required
def alerts():
    now = datetime.utcnow()
    three_hours_ago = now - timedelta(hours=3)

    # 최근 3시간 데이터 가져오기 및 병합
    entry_data = EntryRecognition.query.filter(
        EntryRecognition.recognition_time >= three_hours_ago
    )
    exit_data = ExitRecognition.query.filter(
        ExitRecognition.recognition_time >= three_hours_ago
    )

    # 병합된 데이터 쿼리로 변환 (모델 간 직접 병합은 SQLAlchemy에서 불가능하므로 정렬을 위해 리스트 변환 후 처리)
    combined_data = entry_data.union(exit_data).order_by(EntryRecognition.recognition_time.desc())

    # 페이지네이션 처리
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 한 페이지당 항목 수
    paginated_data = combined_data.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'alerts.html',
        all_data=paginated_data.items,  # 현재 페이지 항목
        page=paginated_data.page,  # 현재 페이지 번호
        total_pages=paginated_data.pages  # 전체 페이지 수
    )


# -------------------------------
# 기타 사항 / 환경 설정
# -------------------------------

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # 환경 설정 처리 로직
    setting = Setting.query.first()
    if request.method == 'POST':
        fee = request.form.get('fee_per_10_minutes', type=int)
        total_slots = request.form.get('total_parking_slots', type=int)
        total_floors = request.form.get('total_floors', type=int)

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
    # 허용된 카테고리와 모델 매핑
    allowed_categories = {
        'entry': EntryRecognition,
        'exit': ExitRecognition,
        'light_vehicle': LightVehicleRecognition,
        'disabled_vehicle': DisabledVehicleRecognition,
        'illegal_parking': IllegalParkingVehicleRecognition,
    }

    # 카테고리 검증
    if category not in allowed_categories:
        flash("유효하지 않은 카테고리입니다.", "danger")
        return redirect(url_for('search'))

    model = allowed_categories[category]
    data = model.query.all()

    # 데이터프레임 생성
    df = pd.DataFrame([{
        '차량 번호': record.vehicle_number,
        '핸드폰 번호': record.phone_number,
        '인식 시간': record.recognition_time.strftime('%Y-%m-%d %H:%M:%S') if record.recognition_time else None,
        '이미지 경로': record.image_path
    } for record in data])

    # 카테고리별 폴더 생성
    folder_path = os.path.join('static', category)
    os.makedirs(folder_path, exist_ok=True)  # 폴더가 없으면 생성

    # PDF로 내보내기
    if file_format == 'pdf':
        file_path = os.path.join(folder_path, f'{category}_data.pdf')
        pdf = FPDF()
        pdf.add_page()

        # 폰트 설정 (유니코드 지원)
        font_path = os.path.join('static', 'fonts', 'NanumGothic.ttf')
        pdf.add_font('NotoSans', '', font_path, uni=True)
        pdf.set_font('NotoSans', size=12)

        # PDF 제목
        pdf.cell(200, 10, txt=f"{category.capitalize()} Data", ln=True, align='C')

        # 데이터 추가
        for index, row in df.iterrows():
            pdf.cell(200, 10, txt=str(row.to_dict()), ln=True)

        pdf.output(file_path)
        return send_file(file_path, as_attachment=True)

    # Excel로 내보내기
    elif file_format == 'excel':
        file_path = os.path.join(folder_path, f'{category}_data.xlsx')
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    # 유효하지 않은 파일 형식 처리
    flash("유효하지 않은 파일 형식입니다.", "danger")
    return redirect(url_for('search'))

# -------------------------------
# 관리자 이메일 가져오는 라우트
# -------------------------------

from flask import g

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
