<script>
    const videoFeed = document.getElementById("videoFeed");
    const startButton = document.getElementById("startButton");
    const stopButton = document.getElementById("stopButton");
    const captureButton = document.getElementById("captureButton");
    const ocrResults = document.getElementById("ocrResults");
    const capturedImage = document.getElementById("capturedImage");
    const ocrSection = document.querySelector(".ocr-results-section");
    const imageSection = document.querySelector(".captured-image-section");

    let webcamStream = null;

    // 웹캠 시작
    startButton.addEventListener("click", () => {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((stream) => {
                videoFeed.srcObject = stream;
                webcamStream = stream;

                startButton.style.display = "none";
                stopButton.style.display = "block";
                captureButton.style.display = "block";
            })
            .catch((err) => console.error("웹캠 시작 오류:", err));
    });

    // 웹캠 종료
    stopButton.addEventListener("click", () => {
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            videoFeed.srcObject = null;
        }

        startButton.style.display = "block";
        stopButton.style.display = "none";
        captureButton.style.display = "none";
        ocrSection.style.display = "none";
        imageSection.style.display = "none";
    });

    // 이미지 캡처 및 OCR 실행
    captureButton.addEventListener("click", () => {
        const canvas = document.createElement("canvas");
        canvas.width = videoFeed.videoWidth;
        canvas.height = videoFeed.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);
    
        const imageData = canvas.toDataURL("image/jpeg");
    
        fetch("/capture-image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_data: imageData })
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === "success") {
                    // 캡처된 이미지 출력 (이미지는 숨기기 위해 src는 설정하지만 보이지 않도록)
                    capturedImage.src = data.image_path;
                    imageSection.style.display = "none";  // 이미지 섹션 숨기기
    
                    // OCR 결과 출력
                    ocrResults.innerHTML = data.ocr_text.map(text => `<li>${text}</li>`).join("");
                    ocrSection.style.display = "block";  // OCR 결과 섹션 보이기
                } else {
                    alert("OCR 실패: " + data.error);
                }
            })
            .catch((err) => console.error("이미지 전송 오류:", err));
    });

</script>