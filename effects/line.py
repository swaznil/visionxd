import cv2


def run(frame, results):

    h, w, _ = frame.shape

    if results.multi_hand_landmarks and len(results.multi_hand_landmarks) >= 2:

        hand1 = results.multi_hand_landmarks[0]
        hand2 = results.multi_hand_landmarks[1]

        p1 = hand1.landmark[8]
        p2 = hand2.landmark[8]

        x1 = int(p1.x * w)
        y1 = int(p1.y * h)

        x2 = int(p2.x * w)
        y2 = int(p2.y * h)

        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 8)

    return frame