from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file, Response
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import relationship
from fpdf import FPDF
import cv2
import easyocr
import torch
import pandas as pd
import openpyxl
import os

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# MySQL 연결 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/cctv_db'  # 실제 MySQL 계정 및 데이터베이스명으로 수정
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 및 Bcrypt 초기화
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 로그인 확인을 위한 데코레이터
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# 웹캡 초기화 (기본카메라 사용 0)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        # 웹캠에서 프레임 읽기
        success, frame = camera.read()
        if not success:
            break
        else:
            # 프레임을 JPEG 형식으로 인코딩
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 프레임 반환
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
# 사용자 모델 생성
class User(db.Model):
    __tablename__ = 'users'  # 테이블 이름 명시
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)  # name에 UNIQUE 제약조건 추가
    phone = db.Column(db.String(20), nullable=False)

    # User와 Report 간의 관계 설정 (user_name을 name으로 연결)
    reports = relationship('Report', backref='user', primaryjoin="foreign(Report.user_name) == User.name", lazy=True)


# 보고서 모델 생성
class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    entry_count = db.Column(db.Integer, default=0)
    exit_count = db.Column(db.Integer, default=0)
    current_parking_count = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, nullable=True)  # DATETIME 형식
    end_time = db.Column(db.DateTime, nullable=True)  # DATETIME 형식
    total_fee = db.Column(db.Integer, default=0)  # 정수형으로 변경
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # 사용자 이름 (외래 키 없이 직접 참조)
    user_name = db.Column(db.String(80), nullable=False)  # 사용자 이름을 저장

# 입차 인식 모델 생성
class EntryRecognition(db.Model):
    __tablename__ = 'entry_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)

# 출차 인식 모델 생성
class ExitRecognition(db.Model):
    __tablename__ = 'exit_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)

# 경차 인식 모델 생성
class LightVehicleRecognition(db.Model):
    __tablename__ = 'light_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)

# 장애인 차량 인식 모델 생성
class DisabledVehicleRecognition(db.Model):
    __tablename__ = 'disabled_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)

# 불법 주차 차량 인식 모델 생성
class IllegalParkingVehicleRecognition(db.Model):
    __tablename__ = 'illegal_parking_vehicle_recognition'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    recognition_time = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/entry-recognition-data')
@login_required
def entry_recognition_data():
    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10  # 한 페이지당 표시할 데이터 수

    # 데이터 가져오기 및 페이지네이션 적용
    paginated_data = EntryRecognition.query.order_by(EntryRecognition.recognition_time.desc()) \
                                           .paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿으로 데이터 전달
    return render_template(
        'entry_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )


@app.route('/exit-recognition-data')
@login_required
def exit_recognition_data():
    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10  # 한 페이지당 표시할 데이터 수

    # 데이터 가져오기 및 페이지네이션 적용
    paginated_data = ExitRecognition.query.order_by(ExitRecognition.recognition_time.desc()) \
                                          .paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿으로 데이터 전달
    return render_template(
        'exit_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )


@app.route('/light-vehicle-recognition-data')
@login_required
def light_vehicle_recognition_data():
    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10  # 한 페이지당 표시할 데이터 수

    # 데이터 가져오기 및 페이지네이션 적용
    paginated_data = LightVehicleRecognition.query.order_by(LightVehicleRecognition.recognition_time.desc()) \
                                                 .paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿으로 데이터 전달
    return render_template(
        'light_vehicle_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )


@app.route('/disabled-vehicle-recognition-data')
@login_required
def disabled_vehicle_recognition_data():
    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10  # 한 페이지당 표시할 데이터 수

    # 데이터 가져오기 및 페이지네이션 적용
    paginated_data = DisabledVehicleRecognition.query.order_by(DisabledVehicleRecognition.recognition_time.desc()) \
                                                     .paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿으로 데이터 전달
    return render_template(
        'disabled_vehicle_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )


@app.route('/illegal-parking-vehicle-recognition-data')
@login_required
def illegal_parking_vehicle_recognition_data():
    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10  # 한 페이지당 표시할 데이터 수

    # 데이터 가져오기 및 페이지네이션 적용
    paginated_data = IllegalParkingVehicleRecognition.query.order_by(IllegalParkingVehicleRecognition.recognition_time.desc()) \
                                                           .paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿으로 데이터 전달
    return render_template(
        'illegal_parking_vehicle_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages
    )


# 시간 포맷팅
def formatted_start_time(self):
    if self.start_time:
        return self.start_time.strftime('%Y-%m-%d %H:%M')  # 시작 시간 포맷
    return '공백'

def formatted_end_time(self):
    if self.end_time:
        return self.end_time.strftime('%Y-%m-%d %H:%M')  # 끝 시간 포맷
    return '공백'

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()  # 사용자 검색

        if user and bcrypt.check_password_hash(user.password, password):  # 비밀번호 검증
            session['logged_in'] = True
            session['username'] = username
            session['name'] = user.name  # `name`도 세션에 저장
            flash('로그인 성공!', 'success')
            return redirect(url_for('home'))
        else:
            flash('아이디나 비밀번호가 잘못되었습니다.', 'danger')

    return render_template('login.html')

# 로그아웃 처리
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)  # 세션에서 'logged_in'을 제거
    session.pop('username', None)  # 세션에서 'username'을 제거
    flash("로그아웃되었습니다.", "info")  # 로그아웃 메시지 표시
    return redirect(url_for('login'))  # 로그인 페이지로 리디렉션

# 회원가입 처리
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        phone = request.form['phone']

        # 비밀번호 해싱
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 사용자 객체 생성
        new_user = User(username=username, password=hashed_password, email=email, name=name, phone=phone)

        # DB에 사용자 추가
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('회원가입 성공!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'오류 발생: {e}', 'danger')

    return render_template('signup.html')

#대시보드
@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return f"Welcome {session['username']}!"

# CCTV 영상을 실시간으로 스트리밍하는 제너레이터 함수
def gen():
    cap = cv2.VideoCapture("")  # 나중에 주소 입력
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        _, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# 홈 페이지
@app.route('/')
def home():
    if 'logged_in' in session:
        return render_template('home.html')  # 로그인된 상태일 때 홈 화면을 렌더링
    return redirect(url_for('login'))  # 로그인되지 않으면 로그인 페이지로 리디렉션

@app.route('/<category>_recognition_list')
@login_required
def recognition_list(category):
    # 카테고리 매핑
    allowed_categories = {
        'entry': ('입차 인식', EntryRecognition),
        'exit': ('출차 인식', ExitRecognition),
        'light_vehicle': ('경차 인식', LightVehicleRecognition),
        'disabled_vehicle': ('장애인 차량 인식', DisabledVehicleRecognition),
        'illegal_parking': ('불법 주차 차량 인식', IllegalParkingVehicleRecognition)
    }

    # 카테고리 유효성 검사
    if category not in allowed_categories:
        flash("Invalid category!", "danger")
        return redirect(url_for('search'))

    # 페이지 번호 가져오기 (기본값: 1)
    page = request.args.get('page', default=1, type=int)
    per_page = 10

    # 카테고리 이름과 모델 분리
    category_name, model = allowed_categories[category]

    # 데이터 조회 및 페이지네이션
    paginated_data = model.query.order_by(model.recognition_time.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # 템플릿 렌더링
    return render_template(
        f'{category}_recognition_list.html',
        data=paginated_data.items,
        page=paginated_data.page,
        total_pages=paginated_data.pages,
        category_name=category_name
    )


# 검색 리스트 페이지
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

# 검색 결과 페이지
@app.route('/search-results', methods=['GET', 'POST'])
@login_required
def search_results():
    query = None
    results = []

    if request.method == 'POST':
        # 폼에서 입력된 차량 번호 4자리 검색 쿼리를 가져옴
        query = request.form.get('query', '').strip()

        if query and len(query) == 4 and query.isdigit():
            # 모든 테이블에서 해당 번호가 포함된 차량 데이터를 검색
            results = {
                '입차 인식': EntryRecognition.query.filter(EntryRecognition.vehicle_number.like(f'%{query}%')).all(),
                '출차 인식': ExitRecognition.query.filter(ExitRecognition.vehicle_number.like(f'%{query}%')).all(),
                '경차 인식': LightVehicleRecognition.query.filter(LightVehicleRecognition.vehicle_number.like(f'%{query}%')).all(),
                '장애인 차량 인식': DisabledVehicleRecognition.query.filter(DisabledVehicleRecognition.vehicle_number.like(f'%{query}%')).all(),
                '불법 주차 차량 인식': IllegalParkingVehicleRecognition.query.filter(IllegalParkingVehicleRecognition.vehicle_number.like(f'%{query}%')).all()
            }

    return render_template('search_results.html', query=query, results=results)


# 알람 현황 페이지
@app.route('/alerts')
@login_required  # 로그인된 사용자만 접근 가능
def alerts():
    return render_template('alerts.html')

# 긴급 상황 페이지
@app.route('/emergencies')
@login_required  # 로그인된 사용자만 접근 가능
def emergencies():
    return render_template('emergencies.html')

# 보고서 페이지 및 데이터 입력, 표시
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    user_name = session['username']  # 로그인된 사용자의 이름 가져오기

    # 초기 값 설정
    start_time = None
    end_time = None

    if request.method == 'POST':
        # 출근 버튼 클릭 시 start_time 설정
        if 'start_time_button' in request.form:
            # 퇴근하지 않은 상태인 보고서가 있는지 확인
            existing_report = Report.query.filter_by(user_name=user_name, end_time=None).first()
            
            if existing_report:
                # 퇴근하지 않은 상태에서 출근을 시도할 수 없음
                flash("현재 퇴근하지 않은 상태입니다. 퇴근 후 출근을 할 수 있습니다.", "danger")
            else:
                # 출근 시간은 현재 시간으로 기록 (초 포함)
                start_time = datetime.now()  # 초 단위 포함
                # 새로 출근 기록 생성
                new_report = Report(
                    entry_count=0,
                    exit_count=0,
                    current_parking_count=0,
                    start_time=start_time,
                    end_time=None,  # end_time은 아직 없음
                    total_fee=0,
                    user_name=user_name
                )
                db.session.add(new_report)
                db.session.commit()
                flash("출근 시간이 기록되었습니다!", "success")
        
        # 보고서 작성(퇴근) 버튼 클릭 시 end_time 설정
        elif 'end_time_button' in request.form:
            # 퇴근 시간은 현재 시간으로 기록
            end_time = datetime.now()  # 초 포함
            
            # 출근 시간이 기록되지 않은 보고서를 찾음
            report = Report.query.filter_by(user_name=user_name, end_time=None).order_by(Report.start_time.asc()).first()
            
            if report:
                # 해당 출근 기록에 end_time을 추가하고 나머지 필드를 채워서 새로 저장
                report.end_time = end_time
                report.total_fee = 0  # 예시로 총 요금 설정, 필요한 대로 수정
                db.session.commit()
                
                flash("퇴근 시간이 기록되었습니다!", "success")
            else:
                flash("출근 기록이 없습니다. 출근 버튼을 먼저 눌러주세요.", "danger")

            # 보고서 작성 후 1페이지로 리디렉션
            return redirect(url_for('report', page=1))

    # GET 요청 시 보고서 목록 가져오기
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(user_name=user_name).order_by(Report.start_time.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template('report.html', reports=reports)




# 보안 / 로그인 페이지
@app.route('/security',  methods=['GET', 'POST'])
@login_required  # 로그인된 사용자만 접근 가능
def security():
    # 관리자 권한 확인
    if session['username'] != 'admin':  # 예시: 'admin'이 관리자 아이디로 설정
        flash("관리자 권한이 필요합니다.", "danger")
        return redirect(url_for('home'))  # 관리자만 접근 가능

    # 모든 사용자 정보 조회
    users = User.query.all()

    if request.method == 'POST':
        # 사용자 삭제 요청 처리
        user_id_to_delete = request.form.get('user_id_to_delete')
        user_to_delete = User.query.get(user_id_to_delete)
        
        if user_to_delete:
            try:
                db.session.delete(user_to_delete)
                db.session.commit()
                flash(f"사용자 '{user_to_delete.username}'가 삭제되었습니다.", "success")
            except Exception as e:
                db.session.rollback()
                flash("사용자 삭제에 실패했습니다.", "danger")

    return render_template('security.html', users=users)

# 환경 설정 페이지
@app.route('/settings')
@login_required  # 로그인된 사용자만 접근 가능
def settings():
    return render_template('settings.html')

# 입차 인식
@app.route('/entry-recognition')
@login_required  # 로그인된 사용자만 접근 가능
def entry_recognition():
    # 이미지 경로 설정
    image_path = r"D:\AI3\study\flask_study\cctv\py\carimg.jpg"
    original_image_save_path = r"static/images/original_image.jpg"
    enhanced_image_save_path = r"static/images/enhanced_image.jpg"
    
    # OpenCV로 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        flash("이미지를 불러올 수 없습니다. 경로를 확인하세요.", "danger")
        return redirect(url_for('home'))

    # 원본 이미지를 저장
    cv2.imwrite(original_image_save_path, image)

    # 그레이스케일 변환
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 대비 조정
    enhanced_image = cv2.convertScaleAbs(gray_image, alpha=1.5, beta=0)

    # 처리된 이미지 저장
    cv2.imwrite(enhanced_image_save_path, enhanced_image)

    # OCR 실행
    reader = easyocr.Reader(['en', 'ko'])
    result = reader.readtext(enhanced_image)

    # OCR 결과 추출
    ocr_results = []
    for detection in result:
        text = detection[1]  # 인식된 텍스트
        ocr_results.append(text)

    # 결과를 템플릿에 전달
    return render_template(
        'entry_recognition.html',
        ocr_results=ocr_results,
        original_image='images/original_image.jpg',
        enhanced_image='images/enhanced_image.jpg'
    )

# 출차 인식 
@app.route('/exit-recognition')
@login_required  # 로그인된 사용자만 접근 가능
def exit_recognition():
    return render_template('exit_recognition.html')

# 출차 비디오 피드
@app.route('/exit-recognition-feed')
def exit_video_feed():
    # 비디오 피드 스트림 생성
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# 경차 인식
@app.route('/light-vehicle-recognition')
@login_required  # 로그인된 사용자만 접근 가능
def light_vehicle_recognition():
    return render_template('light-vehicle-recognition.html')

# 장애인 차량 인식
@app.route('/disabled-vehicle-recognition')
@login_required  # 로그인된 사용자만 접근 가능
def disabled_vehicle_recognition():
    return render_template('disabled-vehicle-recognition.html')

# 불법주차 차량 인식
@app.route('/illegal-parking-recognition')
@login_required  # 로그인된 사용자만 접근 가능
def illegal_parking_vehicle_recognition():
    return render_template('illegal-parking-recognition.html')
        
# PDF, EXEL 저장
@app.route('/export/<string:category>/<string:file_format>', methods=['GET'])
@login_required
def export_category_data(category, file_format):
    # 카테고리 모델 매핑
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

    # 데이터 가져오기
    model = allowed_categories[category]
    data = model.query.all()

    # 데이터 프레임 생성
    df = pd.DataFrame([{
        '차량 번호': d.vehicle_number if hasattr(d, 'vehicle_number') else None,
        '핸드폰 번호': d.phone_number if hasattr(d, 'phone_number') else None,
        '인식 시간': d.recognition_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(d, 'recognition_time') and d.recognition_time else None
    } for d in data])

    if file_format == 'pdf':
        # PDF 생성
        file_path = f'{category}_data.pdf'
        pdf = FPDF()
        pdf.add_page()

        # 유니코드 폰트 추가
        font_path = os.path.join('static', 'fonts', 'NanumGothic.ttf')
        pdf.add_font('Nanum', '', font_path, uni=True)
        pdf.set_font('Nanum', size=12)

        # PDF 내용 작성
        pdf.cell(200, 10, txt=f"{category.capitalize()} Data", ln=True, align='C')
        for index, row in df.iterrows():
            pdf.cell(200, 10, txt=f"{row.to_dict()}", ln=True)
        pdf.output(file_path)
        return send_file(file_path, as_attachment=True)

    elif file_format == 'excel':
        # Excel 생성
        file_path = f'{category}_data.xlsx'
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    flash("Invalid file format!", "danger")
    return redirect(url_for('search'))


            


# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
