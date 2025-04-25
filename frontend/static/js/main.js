// main.js
let currentCameraId = 0;
let streamInterval;

// 登录功能
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) throw new Error('登录失败');
        return response.json();
    })
    .then(data => {
        localStorage.setItem('token', data.access_token);
        document.getElementById('loginContainer').classList.add('hidden');
        document.getElementById('videoPanel').classList.remove('hidden');
        startVideoStream(data.access_token);
    })
    .catch(error => alert('用户名或密码错误'));
});

// 注册功能
document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        if (response.status === 201) {
            document.getElementById('registerContainer').classList.add('hidden');
            document.getElementById('loginContainer').classList.remove('hidden');
        }
    });
});

// 界面切换
document.getElementById('registerLink').addEventListener('click', () => {
    document.getElementById('loginContainer').classList.add('hidden');
    document.getElementById('registerContainer').classList.remove('hidden');
});

document.getElementById('loginLink').addEventListener('click', () => {
    document.getElementById('registerContainer').classList.add('hidden');
    document.getElementById('loginContainer').classList.remove('hidden');
});

// 视频流功能
function startVideoStream(token) {
    fetch('/available_cameras', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        if(data.available_cameras.length === 0) {
            alert('没有可用的摄像头');
            return;
        }
        currentCameraId = data.current_camera;
        initVideoStream(token, currentCameraId);
        setupCameraControls(data.available_cameras);
    })
    .catch(error => {
        console.error('摄像头列表获取失败:', error);
        alert('无法获取摄像头信息');
    });
}

function initVideoStream(token, camId) {
    const img = document.createElement('img');
    img.id = 'videoStream';
    img.className = 'live-feed';

    const videoUrl = `/video_feed/${camId}?token=${token}&ts=${Date.now()}`;
    img.src = videoUrl;

    img.onerror = function() {
        console.log('视频流中断，尝试重新连接...');
        this.src = `${videoUrl}&retry=${Date.now()}`;
    };

    videoContainer.innerHTML = '';
    videoContainer.appendChild(img);

    streamInterval = setInterval(() => {
        if(img.naturalWidth === 0) {
            img.src = `${videoUrl}&ping=${Date.now()}`;
        }
    }, 5000);
}

function setupCameraControls(cameras) {
    const controls = document.createElement('div');
    controls.className = 'camera-controls';

    cameras.forEach(camId => {
        const btn = document.createElement('button');
        btn.textContent = `摄像头 ${camId}`;
        btn.onclick = () => switchCamera(camId);
        controls.appendChild(btn);
    });

    videoContainer.prepend(controls);
}

function switchCamera(newCamId) {
    const token = localStorage.getItem('token');
    currentCameraId = newCamId;
    const img = document.getElementById('videoStream');
    img.src = `/video_feed/${newCamId}?token=${token}&ts=${Date.now()}`;
}

// 退出功能
document.getElementById('logoutButton').addEventListener('click', () => {
    localStorage.removeItem('token');
    document.getElementById('videoPanel').classList.add('hidden');
    document.getElementById('loginContainer').classList.remove('hidden');
    clearInterval(streamInterval);
});