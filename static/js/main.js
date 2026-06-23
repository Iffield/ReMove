// 8-bit Audio Synthesizer
function playSound(type) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const playTone = (freq, wtype, time, duration) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = wtype;
        osc.frequency.setValueAtTime(freq, time);
        gain.gain.setValueAtTime(0.1, time);
        gain.gain.exponentialRampToValueAtTime(0.01, time + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(time);
        osc.stop(time + duration);
    };

    const now = audioCtx.currentTime;
    if (type === 'success') {
        playTone(880, 'square', now, 0.1);
        playTone(1200, 'square', now + 0.1, 0.15);
    } else if (type === 'error') {
        playTone(200, 'sawtooth', now, 0.2);
        playTone(150, 'sawtooth', now + 0.2, 0.3);
    }
}

let trackingData = null;
let aimlabAnimFrame = null;

document.getElementById('start-btn').addEventListener('click', () => {
    const fileInput = document.getElementById('video-upload');
    const loadingText = document.getElementById('loading-text');
    const progressBar = document.getElementById('upload-progress');
    const progressContainer = document.getElementById('upload-progress-container');
    const resultsSection = document.getElementById('results-section');
    const replaySection = document.getElementById('video-replay-section');
    const replayVideo = document.getElementById('replay-video');
    const canvas = document.getElementById('aimlab-canvas');
    const ctx = canvas.getContext('2d');
    
    if (fileInput.files.length === 0) {
        alert('กรุณาเลือกไฟล์วิดีโอก่อนครับ!');
        playSound('error');
        return;
    }
    
    const file = fileInput.files[0];
    
    const videoUrl = URL.createObjectURL(file);
    replayVideo.src = videoUrl;
    replaySection.style.display = 'block';
    
    // Draw waiting text on canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f7d51d';
    ctx.font = "20px Tahoma";
    ctx.textAlign = "center";
    ctx.fillText("กำลังวิเคราะห์ข้อมูล... (รอสักครู่)", canvas.width/2, canvas.height/2);
    
    const formData = new FormData();
    formData.append('video', file);
    
    progressContainer.style.display = 'block';
    resultsSection.style.display = 'none';
    loadingText.innerText = "กำลังอัปโหลดวิดีโอ...";
    progressBar.value = 0;
    trackingData = null;
    
    let fakeProgressInterval;
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    
    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            if (percentComplete === 100) {
                loadingText.innerText = "กำลังใช้ AI ประมวลผลและสร้าง Tracking...";
                let p = 0;
                fakeProgressInterval = setInterval(() => {
                    p += (95 - p) * 0.1; 
                    progressBar.value = p;
                }, 500);
            } else {
                progressBar.value = percentComplete;
            }
        }
    };
    
    xhr.onload = () => {
        clearInterval(fakeProgressInterval);
        progressBar.value = 100;
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.setAttribute('value', 0);
            
            if (xhr.status >= 200 && xhr.status < 300) {
                const data = JSON.parse(xhr.responseText);
                trackingData = data; 
                resultsSection.style.display = 'block';
                playSound('success');
                renderResults(data);
                startAimlabReplay();
            } else {
                alert('เกิดข้อผิดพลาด: ' + xhr.responseText);
                playSound('error');
            }
        }, 500); 
    };
    
    xhr.onerror = () => {
        clearInterval(fakeProgressInterval);
        progressContainer.style.display = 'none';
        alert('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย');
        playSound('error');
    };
    
    xhr.send(formData);
});

function startAimlabReplay() {
    if (!trackingData) return;
    const video = document.getElementById('replay-video');
    const canvas = document.getElementById('aimlab-canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = trackingData.video_width || 640;
    canvas.height = trackingData.video_height || 480;
    
    function drawLoop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.strokeStyle = "rgba(255,255,255,0.1)";
        ctx.lineWidth = 2;
        for(let i=1; i<3; i++) {
            ctx.beginPath();
            ctx.moveTo((canvas.width/3)*i, 0);
            ctx.lineTo((canvas.width/3)*i, canvas.height);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(0, (canvas.height/3)*i);
            ctx.lineTo(canvas.width, (canvas.height/3)*i);
            ctx.stroke();
        }
        
        if (video.duration > 0 && trackingData.full_path_left && trackingData.full_path_left.length > 0) {
            const progress = video.currentTime / video.duration;
            let frameIdx = Math.floor(progress * trackingData.full_path_left.length);
            if (frameIdx >= trackingData.full_path_left.length) frameIdx = trackingData.full_path_left.length - 1;
            
            const lPoint = trackingData.full_path_left[frameIdx];
            if (lPoint) {
                ctx.beginPath();
                ctx.arc(lPoint[0], lPoint[1], 15, 0, 2 * Math.PI);
                ctx.fillStyle = '#ff6384';
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#fff';
                ctx.stroke();
            }
            
            const rPoint = trackingData.full_path_right[frameIdx];
            if (rPoint) {
                ctx.beginPath();
                ctx.arc(rPoint[0], rPoint[1], 15, 0, 2 * Math.PI);
                ctx.fillStyle = '#36a2eb';
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#fff';
                ctx.stroke();
            }
        }
        
        aimlabAnimFrame = requestAnimationFrame(drawLoop);
    }
    
    if(aimlabAnimFrame) cancelAnimationFrame(aimlabAnimFrame);
    drawLoop();
}

function renderResults(data) {
    const setStatus = (side, score) => {
        const hpBar = document.getElementById(`${side}-hp`);
        const hpTxt = document.getElementById(`${side}-score-txt`);
        hpBar.value = score;
        hpTxt.innerText = `HP: ${score}/100`;
        
        hpBar.className = 'nes-progress';
        if (score < 40) hpBar.classList.add('is-error');
        else if (score < 70) hpBar.classList.add('is-warning');
        else hpBar.classList.add('is-success');
    };
    
    setStatus('left', data.left_score);
    setStatus('right', data.right_score);
    
    const ctx = document.getElementById('radarChart').getContext('2d');
    if(window.myRadar) window.myRadar.destroy();
    
    Chart.defaults.font.family = "'Tahoma', sans-serif";
    Chart.defaults.font.size = 14;
    Chart.defaults.color = '#ffffff';
    
    window.myRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [['ความเร็ว', '(Speed)'], ['ความแม่นยำ', '(Accuracy)'], ['คุณภาพ', '(Quality)']],
            datasets: [{
                label: 'แขนซ้าย',
                data: [data.left_speed, data.left_accuracy, data.left_quality],
                backgroundColor: 'rgba(255, 99, 132, 0.4)',
                borderColor: 'rgba(255, 99, 132, 1)',
                pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                pointRadius: 4
            }, {
                label: 'แขนขวา',
                data: [data.right_speed, data.right_accuracy, data.right_quality],
                backgroundColor: 'rgba(54, 162, 235, 0.4)',
                borderColor: 'rgba(54, 162, 235, 1)',
                pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: 10
            },
            scales: { 
                r: { 
                    min: 0, 
                    max: 100, 
                    ticks: { stepSize: 20, color: '#fff', backdropColor: 'transparent', font: {size: 10} },
                    grid: { color: 'rgba(255, 255, 255, 0.2)' },
                    angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
                    pointLabels: { color: '#f7d51d', font: { size: 14, weight: 'bold' } }
                } 
            },
            plugins: {
                legend: { labels: { color: '#fff', font: { size: 14 } } }
            }
        }
    });
    
    const drawHitmap = (canvasId, matrix) => {
        const canvas = document.getElementById(canvasId);
        const cCtx = canvas.getContext('2d');
        const s = canvas.width / 20; 
        
        cCtx.clearRect(0, 0, canvas.width, canvas.height);
        
        let maxVal = 1;
        for (let r of matrix) for (let v of r) if (v > maxVal) maxVal = v;
        
        for (let y = 0; y < 20; y++) {
            for (let x = 0; x < 20; x++) {
                const val = matrix[y][x];
                if (val > 0) {
                    const intensity = val / maxVal;
                    const g = Math.floor(255 * (1 - intensity));
                    cCtx.fillStyle = `rgba(255, ${g}, 0, ${0.4 + intensity * 0.6})`; 
                    cCtx.fillRect(x * s, y * s, s, s);
                }
            }
        }
    };
    
    drawHitmap('hitmap-left', data.hitmap_left);
    drawHitmap('hitmap-right', data.hitmap_right);
    
    let thDiagnosis = "";
    if (data.diagnosis === 'Natural Left-handed') thDiagnosis = 'ถนัดซ้ายธรรมชาติ';
    else if (data.diagnosis === 'Natural Right-handed') thDiagnosis = 'ถนัดขวาธรรมชาติ';
    else if (data.diagnosis === 'Ambidextrous') thDiagnosis = 'ถนัดทั้งสองมือ';
    else if (data.diagnosis === 'Learned Non-Use') thDiagnosis = 'มีภาวะหลีกเลี่ยงการใช้งาน (Learned Non-Use)';
    else thDiagnosis = data.diagnosis;
    
    const typeWriterBox = document.getElementById('typewriter-text');
    typeWriterBox.innerHTML = '';
    
    let diagnosisMsg = `การประเมินผลเสร็จสมบูรณ์\nผลลัพธ์: คนในคลิปมีความถนัดแบบ "${thDiagnosis}"\n`;
    if (data.diagnosis === 'Learned Non-Use') {
        diagnosisMsg += `คำเตือน: ตรวจพบการเคลื่อนไหวที่ไม่สมดุล แขนข้างหนึ่งมีการใช้งานหรือคุณภาพการเคลื่อนไหวต่ำกว่าปกติอย่างมีนัยสำคัญ`;
    } else {
        diagnosisMsg += `การเคลื่อนไหวของคุณสมดุลและอยู่ในเกณฑ์ดีมาก พยายามต่อไป!`;
    }
    
    let i = 0;
    function typeWriter() {
        if (i < diagnosisMsg.length) {
            typeWriterBox.innerHTML += diagnosisMsg.charAt(i) === '\n' ? '<br>' : diagnosisMsg.charAt(i);
            i++;
            setTimeout(typeWriter, 30);
        }
    }
    typeWriter();
}

document.getElementById('save-btn').addEventListener('click', () => {
    const scanlines = document.querySelector('.scanlines');
    scanlines.style.display = 'none';
    
    html2canvas(document.getElementById('capture-area'), {
        backgroundColor: '#111',
        scale: 2
    }).then(canvas => {
        scanlines.style.display = 'block';
        const link = document.createElement('a');
        link.download = 'dexterity-report.png';
        link.href = canvas.toDataURL();
        link.click();
    });
});
