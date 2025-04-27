import cv2 as cv
import mediapipe as mp
import time
import math

mpPose = mp.solutions.pose
mpDraw = mp.solutions.drawing_utils
pose = mpPose.Pose()
capture = cv.VideoCapture(0)

ptime = 0
while True:
    isTrue, img = capture.read()
    img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    result = pose.process(img_rgb)

    if result.pose_landmarks:
        mpDraw.draw_landmarks(img, result.pose_landmarks, mpPose.POSE_CONNECTIONS)
        h, w, c = img.shape
        cx1, cy1, cx2, cy2 = 0, 0, 0, 0

        for id, lm in enumerate(result.pose_landmarks.landmark):
            if id == 32 or id == 31:
                cx1, cy1 = int(lm.x * w), int(lm.y * h)
                cv.circle(img, (cx1, cy1), 15, (0, 0, 0), cv.FILLED)
            if id == 6:
                cx2, cy2 = int(lm.x * w), int(lm.y * h)
                cy2 += 20
                cv.circle(img, (cx2, cy2), 15, (0, 0, 0), cv.FILLED)

        if cx1 and cy1 and cx2 and cy2:
            d = math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
            di = round(d * 0.5)
            
            cv.putText(img, "Height : ", (40, 70), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), thickness=2)
            cv.putText(img, str(di), (180, 70), cv.FONT_HERSHEY_DUPLEX, 1, (255, 255, 0), thickness=2)
            cv.putText(img, "cms", (240, 70), cv.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), thickness=2)

    img = cv.resize(img, (700, 500))
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime
    cv.putText(img, "FPS : ", (40, 30), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), thickness=2)
    cv.putText(img, str(int(fps)), (160, 30), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), thickness=2)
    cv.imshow("Task", img)

    if cv.waitKey(20) & 0xFF == ord('q'):
        break

capture.release()
cv.destroyAllWindows()
