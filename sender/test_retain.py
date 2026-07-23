import threading
import time
import cv2
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

import rclpy
import DR_init

# =====================================================
# Robot Settings
# =====================================================

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL

VELOCITY = 60
ACC = 60

JReady = [0, 0, 90, 0, 90, 0]

# =====================================================
# Gripper
# =====================================================

GRIPPER_NAME = "rg2"
TOOLCHANGER_IP = "192.168.1.1"
TOOLCHANGER_PORT = "502"

# =====================================================
# Vision Parameters
# =====================================================

MIN_AREA = 2500

SOLIDITY_THRESHOLD = 0.9
COMPLEXITY_THRESHOLD = 43

LOWER_YELLOW = np.array([25, 90, 100])
UPPER_YELLOW = np.array([40, 255, 255])

OPEN_KERNEL = np.ones((9, 9), np.uint8)
CLOSE_KERNEL = np.ones((7, 7), np.uint8)

# =====================================================
# Cluster Position
# =====================================================
# 0 | 1
# -----
# 2 | 3

QUADRANT_BASE_POS = {
    0: [433, -76, 150],
    1: [256, -76, 150],
    2: [433,  116, 150],
    3: [256,  116, 150],
}

# =====================================================
# Shared State
# =====================================================

target_clusters = None
is_busy = False

# =====================================================
# Frame 공유 (브라우저 → 파이썬)
# =====================================================

capture_requested = False   # 파이썬이 캡처 요청 플래그
latest_frame      = None    # 브라우저에서 받은 프레임
frame_event       = threading.Event()  # 프레임 도착 대기용
frame_lock        = threading.Lock()

# =====================================================
# Flask 서버 (브라우저와 통신)
# =====================================================

app = Flask(__name__)
CORS(app)  # 브라우저 CORS 허용


@app.route('/capture_ready', methods=['GET'])
def capture_ready():
    """브라우저가 1초마다 폴링 — 캡처 요청 있으면 True 반환"""
    global capture_requested
    return jsonify({'requested': capture_requested})


@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """브라우저가 캡처한 프레임 JPEG를 POST로 전송"""
    global latest_frame, capture_requested

    file = request.files.get('frame')
    if file is None:
        return jsonify({'error': 'no frame'}), 400

    img_array = np.frombuffer(file.read(), dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({'error': 'decode failed'}), 400

    with frame_lock:
        latest_frame      = frame
        capture_requested = False   # 요청 소비

    frame_event.set()  # 대기 중인 vision_check_once 깨우기

    return jsonify({'ok': True})


def start_flask(port=5050):
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    t = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, threaded=True),
        daemon=True
    )
    t.start()
    print(f"[Flask] 브라우저 수신 서버 시작: http://0.0.0.0:{port}")


# =====================================================
# Debug View
# =====================================================

def show_debug_view(vis, yellow_mask=None, occluded_mask=None):
    cv2.imshow("test_retain debug", vis)
    if yellow_mask is not None:
        cv2.imshow("yellow_mask", yellow_mask)
    if occluded_mask is not None:
        cv2.imshow("occluded_mask", occluded_mask)
    print("Press any key on the camera window to continue.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# =====================================================
# Rotated Quadrant
# =====================================================

def get_rotated_quadrant(cx, cy, rect):

    (rx, ry), (rw, rh), angle = rect

    if rw < rh:
        angle += 90

    theta = np.deg2rad(angle)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    dx = cx - rx
    dy = cy - ry

    local_x = dx * cos_t + dy * sin_t
    local_y = -dx * sin_t + dy * cos_t

    # 0 | 1
    # -----
    # 2 | 3

    if local_x < 0 and local_y < 0:
        return 0
    elif local_x >= 0 and local_y < 0:
        return 1
    elif local_x < 0 and local_y >= 0:
        return 2
    else:
        return 3


# =====================================================
# Contour Analysis
# =====================================================

def analyze_contour(cnt):

    area = cv2.contourArea(cnt)
    if area < MIN_AREA:
        return None

    perimeter = cv2.arcLength(cnt, True)
    complexity = (perimeter * perimeter) / area

    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    if hull_area == 0:
        return None

    solidity = area / hull_area

    clustered = False
    if solidity < SOLIDITY_THRESHOLD:
        clustered = True
    if complexity > COMPLEXITY_THRESHOLD:
        clustered = True

    return {
        "area": area,
        "complexity": complexity,
        "solidity": solidity,
        "clustered": clustered,
        "hull": hull,
    }


# =====================================================
# Robot Motion
# =====================================================

def perform_cluster_release(base_xyz):

    from DSR_ROBOT2 import (
        DR_BASE,
        get_current_posx,
        movec,
        movej,
        movel,
        posx,
    )

    bx, by, bz = base_xyz

    current_pos = get_current_posx()[0]
    rx = current_pos[3]
    ry = current_pos[4]
    rz = current_pos[5]

    safe_z = 200
    work_z = 130

    above_target = posx(bx, by, safe_z, rx, ry, rz)
    target       = posx(bx, by, work_z, rx, ry, rz)

    movel(above_target, vel=50, acc=50)
    gripper.close_gripper()
    movel(target, vel=20, acc=20)
    time.sleep(1.0)

    for i in range(1, 4):
        first_mid = posx(bx + (i * 20), by,            work_z, rx, ry, rz)
        first_end = posx(bx,            by + (i * 20), work_z, rx, ry, rz)
        movec(first_mid, first_end, vel=80, acc=80, ref=DR_BASE)

    print("GRIPPER CLOSED")

    gripper.open_gripper()
    time.sleep(1.0)

    movel(above_target, vel=50, acc=50)
    movej(JReady, vel=VELOCITY, acc=ACC)

    print("CLUSTER RELEASE COMPLETE")


# =====================================================
# Vision Check (브라우저에서 프레임 받아서 처리)
# =====================================================

def vision_check_once(debug_view=False, timeout=10):

    global target_clusters, capture_requested

    target_clusters = None
    frame_event.clear()

    # 브라우저에 캡처 요청
    print("[Vision] 브라우저에 캡처 요청 중...")
    capture_requested = True

    # 브라우저가 프레임 보내줄 때까지 대기 (최대 timeout초)
    arrived = frame_event.wait(timeout=timeout)

    if not arrived:
        print("[Vision] 프레임 수신 타임아웃")
        capture_requested = False
        return

    with frame_lock:
        frame = latest_frame.copy()

    print("[Vision] 프레임 수신 완료 → 비전 처리 시작")

    vis = frame.copy()

    # ── HSV ──────────────────────────────────────
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # ── Yellow Mask ──────────────────────────────
    yellow_mask = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    # ── Yellow Contours ───────────────────────────
    yellow_contours, _ = cv2.findContours(
        yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if len(yellow_contours) == 0:
        print("No yellow area")
        if debug_view:
            show_debug_view(vis, yellow_mask)
        return

    # ── Largest Yellow ────────────────────────────
    largest_yellow = max(yellow_contours, key=cv2.contourArea)
    largest_yellow = cv2.convexHull(largest_yellow)

    rect = cv2.minAreaRect(largest_yellow)
    box  = np.intp(cv2.boxPoints(rect))
    cv2.drawContours(vis, [box], 0, (255, 0, 0), 2)

    # ── Sponge Mask ───────────────────────────────
    sponge_mask = np.zeros_like(yellow_mask)
    cv2.drawContours(sponge_mask, [largest_yellow], -1, 255, -1)

    # ── Occluded Area ─────────────────────────────
    occluded_mask = cv2.subtract(sponge_mask, yellow_mask)
    occluded_mask = cv2.morphologyEx(occluded_mask, cv2.MORPH_OPEN,  OPEN_KERNEL,  iterations=2)
    occluded_mask = cv2.morphologyEx(occluded_mask, cv2.MORPH_CLOSE, CLOSE_KERNEL)

    # ── Find Contours ─────────────────────────────
    contours, _ = cv2.findContours(
        occluded_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    single_exist      = False
    cluster_exist     = False
    cluster_positions = []

    # ── Analyze ───────────────────────────────────
    for cnt in contours:

        result = analyze_contour(cnt)
        if result is None:
            continue

        clustered = result["clustered"]

        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        quadrant = get_rotated_quadrant(cx, cy, rect)

        if clustered:
            cluster_exist = True
            cluster_positions.append(quadrant)
            color = (0, 0, 255)
            label = f"cluster q{quadrant}"
        else:
            single_exist = True
            color = (0, 255, 0)
            label = f"single q{quadrant}"

        cv2.drawContours(vis, [cnt], -1, color, 2)
        cv2.circle(vis, (cx, cy), 5, color, -1)
        cv2.putText(vis, label, (cx + 8, cy - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # ── Decision ─────────────────────────────────
    single_not_exist = not single_exist

    print("\n======================")
    print("single_not_exist:", single_not_exist)
    print("cluster_exist:",    cluster_exist)

    if single_not_exist and cluster_exist:
        unique_positions = sorted(list(set(cluster_positions)))
        print("cluster_positions:", unique_positions)
        target_clusters = unique_positions
    else:
        print("No valid cluster condition")

    if debug_view:
        show_debug_view(vis, yellow_mask, occluded_mask)


# =====================================================
# Robot Execute
# =====================================================

def robot_task_loop():

    global target_clusters, is_busy

    print("🔥 robot_task_loop started")

    from DSR_ROBOT2 import movej

    movej(JReady, vel=VELOCITY, acc=ACC)
    gripper.open_gripper()

    if target_clusters is None:
        print("No cluster target")
        return

    if is_busy:
        print("Robot busy")
        return

    is_busy = True

    try:
        print("\n======================")
        print("START ROBOT TASK")
        print("======================")

        for quadrant in target_clusters:
            if quadrant not in QUADRANT_BASE_POS:
                continue
            base_xyz = QUADRANT_BASE_POS[quadrant]
            perform_cluster_release(base_xyz)
            time.sleep(1.0)

    except Exception as e:
        print(f"❌ Robot Error: {e}")

    target_clusters = None
    is_busy = False


# =====================================================
# Run Once
# =====================================================

def run_cluster_check_once(debug_view=False):

    print("\n======================")
    print("VISION CHECK START")
    print("======================")

    vision_check_once(debug_view=debug_view)

    if target_clusters is None:
        print("No cluster detected")
        return

    print("\n======================")
    print("CLUSTER DETECTED")
    print("======================")

    robot_task_loop()


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    # 1. Flask 서버 백그라운드 시작
    start_flask(port=5050)

    print("\n[안내] camera_stream.html 을 브라우저에서 열어주세요")
    print("[안내] HTML 파일 안 ROBOT_SERVER 주소를 이 PC의 IP로 수정하세요")
    print("[안내] 브라우저 준비되면 Enter 누르세요...")
    input()

    # 2. 로봇 작업 실행
    run_cluster_check_once(debug_view=True)
