from flask import Blueprint, render_template, Response, jsonify
import csv
import io

# Không tạo instance ở đây nữa
main_bp = Blueprint('main', __name__)

# Sẽ nhận db_manager từ app.py
db_manager = None

def init_main_routes(db_manager_instance):
    global db_manager
    db_manager = db_manager_instance

@main_bp.route('/')
def index():
    return render_template('video.html')

@main_bp.route('/export_csv')
def export_csv():
    if db_manager is None:
        return Response("Database manager not initialized!", mimetype='text/plain')
    
    attendance_records = db_manager.get_attendance_records()
    
    if not attendance_records:
        return Response("Không có dữ liệu để xuất!", mimetype='text/plain')
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['STT', 'Tên', 'Thời gian', 'Trạng thái'])
    writer.writeheader()
    
    for i, row in enumerate(attendance_records, start=1):
        writer.writerow({
            'STT': i,
            'Tên': row['name'],
            'Thời gian': row['time'],
            'Trạng thái': row['status']
        })

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=attendance.csv'
    return response

@main_bp.route('/reset_attendance', methods=['POST'])
def reset_attendance():
    if db_manager is None:
        return jsonify({'error': 'Database manager not initialized!'}), 500
        
    db_manager.reset_attendance()
    print("✅ Attendance records cleared.")
    return jsonify({'message': 'Danh sách điểm danh đã được xóa'})
