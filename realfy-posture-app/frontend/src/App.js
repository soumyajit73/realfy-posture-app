import React, { useRef, useState } from "react";
import {
  Container,
  Typography,
  Button,
  Box,
  Stack,
  CircularProgress,
  Paper,
} from "@mui/material";
import VideoFileIcon from "@mui/icons-material/VideoFile";
import VideocamIcon from "@mui/icons-material/Videocam";
import StopCircleIcon from "@mui/icons-material/StopCircle";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

function App() {
  const videoRef = useRef(null);
  const fileInputRef = useRef();
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const [webcamActive, setWebcamActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);

  const handleFileUpload = async (event) => {
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
      await uploadVideoToBackend(file);
    }
  };

  const uploadVideoToBackend = async (file) => {
    setUploading(true);
    setAnalysisResults(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload-video/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setAnalysisResults(data);
    } catch (error) {
      console.error("Error uploading video:", error);
      alert("Upload failed.");
    } finally {
      setUploading(false);
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

        recordedChunksRef.current = [];
        mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "video/webm" });
        mediaRecorderRef.current.ondataavailable = (e) => {
          if (e.data.size > 0) {
            recordedChunksRef.current.push(e.data);
          }
        };
        mediaRecorderRef.current.start();
      })
      .catch((err) => {
        console.error("Error accessing webcam:", err);
      });
  };

  const stopWebcam = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(recordedChunksRef.current, { type: "video/webm" });
        const file = new File([blob], "webcam_recording.webm", { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        if (videoRef.current) {
          videoRef.current.srcObject = null;
          videoRef.current.src = url;
          videoRef.current.play();
        }
        await uploadVideoToBackend(file);
      };
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setWebcamActive(false);
  };

  const renderAnalysisSummary = () => {
    if (!analysisResults || !analysisResults.frame_results) {
      return <Typography>No analysis data available.</Typography>;
    }

    const frames = analysisResults.frame_results;
    const totalFrames = frames.length;
    const dominantPosture = analysisResults.posture_type;

    // ✅ Only include frames matching the dominant posture
    const filteredFrames = frames.filter(
      (f) => f.posture_type === dominantPosture
    );

    const badFrames = filteredFrames.filter((f) => f.bad_posture).length;
    const percentageBad = ((badFrames / filteredFrames.length) * 100).toFixed(2);

    // ✅ Count issues from relevant frames only
    const issueCounts = {};
    filteredFrames.forEach((f) => {
      (f.flags || []).forEach((flag) => {
        issueCounts[flag] = (issueCounts[flag] || 0) + 1;
      });
    });

    const chartData = Object.entries(issueCounts).map(([flag, count]) => ({
      name: flag,
      count: count,
    }));

    return (
      <Box mt={4}>
        <Typography variant="h5" gutterBottom>
          Posture Analysis Summary
        </Typography>

        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography>
            Detected Posture Type: <b>{analysisResults.posture_type}</b>
          </Typography>
          <Typography>Total Frames Analyzed: {filteredFrames.length}</Typography>
          <Typography>Frames with Bad Posture: {badFrames}</Typography>
          <Typography>Percentage Bad Posture: {percentageBad}%</Typography>
        </Paper>

        {chartData.length > 0 ? (
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1">Detected Issues</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 50 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={250} />
                <Tooltip />
                <Bar dataKey="count" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        ) : (
          <Typography>No posture issues detected!</Typography>
        )}
      </Box>
    );
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
            Stop & Analyze
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

      {uploading && (
        <Box sx={{ mt: 4 }}>
          <CircularProgress />
          <Typography>Processing video...</Typography>
        </Box>
      )}

      {analysisResults && renderAnalysisSummary()}
    </Container>
  );
}

export default App;