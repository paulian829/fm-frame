import cv2

# Define the RTSP address for the stream
rtsp_url = "rtsp://tapocamera:123456@192.168.1.100:554/stream1"

# Open the stream using OpenCV
cap = cv2.VideoCapture(rtsp_url)

# Check if the stream was opened successfully
if not cap.isOpened():
    print("Error opening stream.")

# Read frames from the stream
while True:
    ret, frame = cap.read()

    # Break the loop if the stream is not opened or the frame is not available
    if not ret:
        break

    # Display the frame
    cv2.imshow("Frame", frame)

    # Break the loop if the "q" key is pressed
    if cv2.waitKey(25) & 0xFF == ord("q"):
        break

# Release the stream and destroy the windows
cap.release()
cv2.destroyAllWindows()
