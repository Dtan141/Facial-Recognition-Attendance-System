const socket = io();

// =======================
// 🎥 Điều khiển camera
// =======================
function startStream() {
  socket.emit('start_stream');
  const status = document.getElementById('status');
  status.textContent = "Đang nhận diện...";
  status.classList.replace('text-muted', 'text-primary');
}

function stopStream() {
  socket.emit('stop_stream');
  const status = document.getElementById('status');
  status.textContent = "Đã dừng camera";
  status.classList.replace('text-primary', 'text-danger');
}

// =======================
// 🔄 Reset & Xuất CSV
// =======================
function resetAttendance() {
  // 🧹 Làm sạch giao diện
  document.getElementById('attendanceTable').innerHTML = '<tr><td colspan="4">Chưa có dữ liệu</td></tr>';
  document.getElementById('studentName').textContent = '—';
  document.getElementById('attendanceTime').textContent = '—';
  const status = document.getElementById('status');
  status.textContent = "Chưa điểm danh";
  status.className = 'text-muted';

  // 🔥 Gửi yêu cầu lên server để xóa dữ liệu thật
  fetch('/reset_attendance', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      console.log(data.message);
      alert('Đã reset danh sách điểm danh!');
    })
    .catch(error => {
      console.error('Lỗi khi reset:', error);
      alert('Không thể reset danh sách.');
    });
}

function exportCSV() {
  fetch('/export_csv')
    .then(response => {
      if (!response.ok) throw new Error("Không thể xuất CSV!");
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'attendance.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    })
    .catch(err => alert(err.message));
}

// =======================
// 🧠 Socket.IO Events
// =======================
socket.on('video_frame', function(data) {
  const img = document.getElementById('video');
  img.src = 'data:image/jpeg;base64,' + data.image;
});

socket.on('recognition_result', function(data) {
  const { name, time, status } = data;

  document.getElementById('studentName').textContent = name;
  document.getElementById('attendanceTime').textContent = time;
  document.getElementById('status').textContent = status;
  document.getElementById('status').className = (status === "Đã điểm danh")
    ? 'text-success'
    : 'text-danger';

  const table = document.getElementById('attendanceTable');
  const newRow = document.createElement('tr');
  newRow.innerHTML = `
    <td>${table.rows.length}</td>
    <td>${name}</td>
    <td>${time}</td>
    <td>${status}</td>
  `;
  if (table.rows[0].cells[0].colSpan === 4) table.innerHTML = "";
  table.appendChild(newRow);
});

// 🔹 Kích hoạt webcam khi mở modal
const registerModal = document.getElementById('registerModal');
const video = document.getElementById('cameraPreview');

registerModal.addEventListener('shown.bs.modal', () => {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => { video.srcObject = stream; })
    .catch(err => console.error("Không thể mở webcam:", err));
});

// 🔹 Tắt webcam khi đóng modal
registerModal.addEventListener('hidden.bs.modal', () => {
  if (video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
  }
});

// // 🔹 Chụp ảnh từ camera
// function capturePhoto() {
//   const canvas = document.getElementById('snapshotCanvas');
//   const context = canvas.getContext('2d');
//   context.drawImage(video, 0, 0, canvas.width, canvas.height);
//   canvas.style.display = 'block';
// }

// // 🔹 Gửi dữ liệu đăng ký
// document.getElementById('registerForm').addEventListener('submit', async (e) => {
//   e.preventDefault();

//   const name = document.getElementById('newName').value;
//   const fileInput = document.getElementById('photoUpload');
//   const canvas = document.getElementById('snapshotCanvas');

//   let formData = new FormData();
//   formData.append('name', name);

//   if (fileInput.files.length > 0) {
//     formData.append('image', fileInput.files[0]);
//   } else {
//     const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
//     formData.append('image', blob, 'snapshot.jpg');
//   }

//   const response = await fetch('/register', { method: 'POST', body: formData });
//   const result = await response.json();
//   alert(result.message);

//   // Đóng modal sau khi đăng ký
//   const modalInstance = bootstrap.Modal.getInstance(registerModal);
//   modalInstance.hide();
// });

// 🔹 Chụp ảnh từ camera
function capturePhoto() {
  const canvas = document.getElementById('snapshotCanvas');
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  canvas.style.display = 'block';
}

// 🔹 Reset form và ảnh khi modal được mở
document.getElementById('registerModal').addEventListener('show.bs.modal', function () {
  // Reset form
  document.getElementById('registerForm').reset();
  
  // Ẩn và clear canvas
  const canvas = document.getElementById('snapshotCanvas');
  canvas.style.display = 'none';
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  
  // Reset file input
  document.getElementById('photoUpload').value = '';
});

// 🔹 Gửi dữ liệu đăng ký
document.getElementById('registerForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const name = document.getElementById('newName').value;
  const fileInput = document.getElementById('photoUpload');
  const canvas = document.getElementById('snapshotCanvas');

  // Kiểm tra xem có ảnh nào được chọn/chụp không
  if (fileInput.files.length === 0 && canvas.style.display === 'none') {
    alert('Vui lòng chụp ảnh hoặc tải ảnh lên!');
    return;
  }

  let formData = new FormData();
  formData.append('name', name);

  try {
    if (fileInput.files.length > 0) {
      formData.append('image', fileInput.files[0]);
    } else {
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
      formData.append('image', blob, 'snapshot.jpg');
    }

    const response = await fetch('/register', { method: 'POST', body: formData });
    const result = await response.json();
    
    if (response.ok) {
      alert(result.message);
      // Reset form sau khi đăng ký thành công
      document.getElementById('registerForm').reset();
      canvas.style.display = 'none';
      const context = canvas.getContext('2d');
      context.clearRect(0, 0, canvas.width, canvas.height);
      
      // Đóng modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
      modal.hide();
    } else {
      alert('Lỗi: ' + result.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Có lỗi xảy ra khi đăng ký!');
  }
});