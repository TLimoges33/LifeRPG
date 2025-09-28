import React, { useState, useRef, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import {
  Mic,
  MicOff,
  Camera,
  Upload,
  Play,
  Pause,
  Square,
  Volume2,
  ImageIcon,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const VoiceImageInput = ({ onHabitCreated, onHabitCompleted }) => {
  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceLoading, setVoiceLoading] = useState(false);

  // Image capture/upload state
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [cameraStream, setCameraStream] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageResult, setImageResult] = useState(null);

  // Refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  // Voice Recording Functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/wav" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error("Error starting recording:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const processVoiceCommand = async () => {
    if (!audioBlob) return;

    setVoiceLoading(true);
    try {
      // For now, simulate voice processing
      // In a real implementation, you'd send the audio to your backend
      // which would use speech-to-text and then NLP processing

      const formData = new FormData();
      formData.append("audio", audioBlob);

      const token = localStorage.getItem("token");
      const response = await fetch("/api/v1/ai/habits/voice-command", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setVoiceTranscript(result.transcript || "Voice command processed!");

        if (result.action === "create_habit" && onHabitCreated) {
          onHabitCreated(result.habit);
        } else if (result.action === "complete_habit" && onHabitCompleted) {
          onHabitCompleted(result.habit_id);
        }
      } else {
        // Simulate processing for demo
        setVoiceTranscript(
          "Voice processing coming soon! Audio recorded successfully."
        );
      }
    } catch (error) {
      console.error("Voice processing error:", error);
      setVoiceTranscript("Voice processing temporarily unavailable.");
    } finally {
      setVoiceLoading(false);
    }
  };

  // Camera Functions
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }, // Use back camera on mobile
      });
      setCameraStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      alert("Could not access camera. Please check permissions.");
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      setImageFile(blob);
      setImagePreview(URL.createObjectURL(blob));
      stopCamera();
    });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const processImage = async () => {
    if (!imageFile) return;

    setImageLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", imageFile);

      const token = localStorage.getItem("token");
      const response = await fetch("/api/v1/ai/habits/image-checkin", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setImageResult(result);

        if (result.habit_completed && onHabitCompleted) {
          onHabitCompleted(result.habit_id);
        }
      } else {
        // Simulate processing for demo
        setImageResult({
          message:
            "Image recognition coming soon! Image uploaded successfully.",
          confidence: 0.95,
          detected_items: ["workout equipment", "healthy food", "book"],
        });
      }
    } catch (error) {
      console.error("Image processing error:", error);
      setImageResult({
        message: "Image processing temporarily unavailable.",
        error: true,
      });
    } finally {
      setImageLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Voice Input Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5 text-blue-600" />
            Voice Commands
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-600 text-sm">
            Try saying: "Create a habit to drink water every morning" or "Mark
            my meditation habit as complete"
          </p>

          <div className="flex items-center gap-4">
            {!isRecording ? (
              <Button
                onClick={startRecording}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Mic className="h-4 w-4 mr-2" />
                Start Recording
              </Button>
            ) : (
              <Button onClick={stopRecording} variant="destructive">
                <Square className="h-4 w-4 mr-2" />
                Stop Recording
              </Button>
            )}

            {audioUrl && (
              <div className="flex items-center gap-2">
                <audio controls src={audioUrl} className="h-8" />
                <Button
                  onClick={processVoiceCommand}
                  disabled={voiceLoading}
                  variant="outline"
                >
                  {voiceLoading ? "Processing..." : "Process Voice"}
                </Button>
              </div>
            )}
          </div>

          {isRecording && (
            <div className="flex items-center gap-2 text-red-600">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
              <span className="text-sm">Recording... Speak your command</span>
            </div>
          )}

          {voiceTranscript && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="flex items-start gap-2">
                <Volume2 className="h-4 w-4 text-blue-600 mt-0.5" />
                <div>
                  <div className="font-semibold text-blue-800">
                    Voice Command Result
                  </div>
                  <div className="text-blue-700">{voiceTranscript}</div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Image Input Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-green-600" />
            Image Check-in
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-600 text-sm">
            Take a photo or upload an image to check-in for habits like
            workouts, meals, or reading.
          </p>

          {/* Camera Controls */}
          {!cameraStream ? (
            <div className="flex gap-2">
              <Button
                onClick={startCamera}
                className="bg-green-600 hover:bg-green-700"
              >
                <Camera className="h-4 w-4 mr-2" />
                Open Camera
              </Button>
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Image
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="relative">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full max-w-md rounded-lg"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={capturePhoto}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Camera className="h-4 w-4 mr-2" />
                  Capture Photo
                </Button>
                <Button onClick={stopCamera} variant="outline">
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />

          {/* Hidden canvas for photo capture */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Image Preview */}
          {imagePreview && (
            <div className="space-y-2">
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full max-w-md rounded-lg border"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={processImage}
                  disabled={imageLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {imageLoading ? "Processing..." : "Analyze Image"}
                </Button>
                <Button
                  onClick={() => {
                    setImageFile(null);
                    setImagePreview(null);
                    setImageResult(null);
                  }}
                  variant="outline"
                >
                  Clear
                </Button>
              </div>
            </div>
          )}

          {/* Image Analysis Result */}
          {imageResult && (
            <div className="p-3 bg-green-50 rounded-lg">
              <div className="flex items-start gap-2">
                {imageResult.error ? (
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                ) : (
                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                )}
                <div>
                  <div className="font-semibold text-green-800">
                    Analysis Result
                  </div>
                  <div className="text-green-700">{imageResult.message}</div>

                  {imageResult.detected_items && (
                    <div className="mt-2">
                      <div className="text-sm font-medium text-green-800">
                        Detected Items:
                      </div>
                      <div className="text-sm text-green-700">
                        {imageResult.detected_items.join(", ")}
                      </div>
                    </div>
                  )}

                  {imageResult.confidence && (
                    <div className="text-sm text-green-600 mt-1">
                      Confidence: {Math.round(imageResult.confidence * 100)}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="h-5 w-5 text-purple-600" />
            Usage Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-purple-800 mb-2">
                Voice Commands
              </h4>
              <ul className="space-y-1 text-gray-600">
                <li>• "Create habit to exercise daily"</li>
                <li>• "Mark meditation as complete"</li>
                <li>• "Show my habit progress"</li>
                <li>• "Remind me to drink water at 9am"</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-purple-800 mb-2">
                Image Check-ins
              </h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Photo of your workout equipment</li>
                <li>• Picture of healthy meal</li>
                <li>• Book you're reading</li>
                <li>• Clean workspace/room</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VoiceImageInput;
