import React, { useRef, useState } from "react";
import { Container, Typography, Button, Box, Stack } from "@mui/material";
import VideoFileIcon from "@mui/icons-material/VideoFile";
import VideocamIcon from "@mui/icons-material/Videocam";
import StopCircleIcon from "@mui/icons-material/StopCircle";

function App() {
  const videoRef = useRef(null);
  const fileInputRef = useRef();
  const [webcamActive, setWebcamActive] = useState(false);
  const streamRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.src = url;
        videoRef.current.play();
      }
      if (streamRef.current) {
        stopWebcam();
      }
    }
  };

  const handleStartWebcam = () => {
    navigator.mediaDevices
      .getUserMedia({ video: { width: 1280, height: 720 } })
      .then((stream) => {
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
        setWebcamActive(true);
      })
      .catch((err) => {
        console.error("Error accessing webcam:", err);
      });
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current.src = "";
    }
    setWebcamActive(false);
  };

  return (
    <Container maxWidth="md" sx={{ textAlign: "center", mt: 5 }}>
      <Typography variant="h4" gutterBottom>
        Realfy Posture App
      </Typography>

      <Stack spacing={2} direction="row" justifyContent="center" sx={{ mt: 4 }}>
        <Button
          variant="contained"
          startIcon={<VideoFileIcon />}
          onClick={() => fileInputRef.current.click()}
        >
          Upload Video
        </Button>

        {!webcamActive ? (
          <Button
            variant="outlined"
            startIcon={<VideocamIcon />}
            onClick={handleStartWebcam}
          >
            Use Webcam
          </Button>
        ) : (
          <Button
            variant="outlined"
            color="error"
            startIcon={<StopCircleIcon />}
            onClick={stopWebcam}
          >
            Stop Webcam
          </Button>
        )}
      </Stack>

      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        style={{ display: "none" }}
        onChange={handleFileUpload}
      />

      <Box mt={4}>
        <video
          ref={videoRef}
          controls
          autoPlay
          style={{
            width: "100%",
            maxWidth: "1280px",
            height: "auto",
            borderRadius: 8,
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          }}
        />
      </Box>
    </Container>
  );
}

export default App;
